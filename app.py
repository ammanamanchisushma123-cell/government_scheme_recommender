import streamlit as st
import sqlite3, hashlib, secrets, os, re, html, time
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
try:
    from twilio.rest import Client
except ImportError:
    Client = None

st.set_page_config(page_title='GovScheme AI', page_icon='🇮🇳', layout='wide')
DB='users.db'
LANGS=['English','తెలుగు','हिन्दी','தமிழ்','ಕನ್ನಡ','മലയാളം','বাংলা','मराठी','ગુજરાતી','ਪੰਜਾਬੀ','ଓଡ଼ିଆ']
STATES=['Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal','Delhi','Jammu and Kashmir','Ladakh','Puducherry']
OCC=['Student','Farmer','Employee','Business','Self-employed','Unemployed','Homemaker','Other']
INC=['Below ₹1 lakh','₹1–3 lakh','₹3–5 lakh','₹5–10 lakh','Above ₹10 lakh']
CAT=['General','OBC','SC','ST','Other']

CATEGORY_COUNTS={
'Agriculture, Rural & Environment':862,'Banking, Financial Services and Insurance':336,
'Business & Entrepreneurship':772,'Education & Learning':1110,'Health & Wellness':286,
'Housing & Shelter':136,'Public Safety, Law & Justice':34,'Science, IT & Communications':121,
'Skills & Employment':401,'Social Welfare & Empowerment':1453,'Sports & Culture':280,
'Transport & Infrastructure':104,'Travel & Tourism':96,'Utility & Sanitation':58,
'Women and Child':470}
MINISTRIES=['Ministry of Agriculture & Farmers Welfare','Ministry of Education',
'Ministry of Health & Family Welfare','Ministry of Rural Development','Ministry of Finance',
'Ministry of Women & Child Development','Ministry of Labour & Employment',
'Ministry of Skill Development & Entrepreneurship','Ministry of Social Justice & Empowerment',
'Ministry of Tribal Affairs','Ministry of Housing & Urban Affairs','Ministry of MSME',
'Ministry of Electronics & Information Technology','Ministry of Road Transport & Highways',
'Ministry of Railways','Ministry of Jal Shakti','Ministry of Environment, Forest & Climate Change',
'Ministry of Youth Affairs & Sports','Ministry of Tourism','Ministry of Commerce & Industry']

L={
'English':dict(home='Home',find='Find Schemes',saved='Saved Schemes',profile='My Profile',ai='AI Assistant',login='Login',create='Create Account',mobile='Mobile Number',password='Password',otp='OTP',send='Send OTP',verify='Verify OTP',forgot='Forgot Password?',name='Full Name',email='Email',state='State',district='District',age='Age',gender='Gender',res='Residence',occupation='Occupation',income='Annual Income',category='Social Category',disability='Disability Status',language='Language',requirement='What support are you looking for?',findme='Find Schemes For Me',results='Schemes Recommended For You',details='View Details',benefits='Benefits',eligibility='Eligibility',documents='Documents Required',application='How to Apply',about='About the Scheme',save='Save',logout='Logout',ask='Ask AI',next='Next',back='Back'),
'తెలుగు':dict(home='హోమ్',find='పథకాలను కనుగొనండి',saved='సేవ్ చేసిన పథకాలు',profile='నా ప్రొఫైల్',ai='AI సహాయకుడు',login='లాగిన్',create='ఖాతా సృష్టించండి',mobile='మొబైల్ నంబర్',password='పాస్‌వర్డ్',otp='OTP',send='OTP పంపండి',verify='OTP నిర్ధారించండి',forgot='పాస్‌వర్డ్ మర్చిపోయారా?',name='పూర్తి పేరు',email='ఈమెయిల్',state='రాష్ట్రం',district='జిల్లా',age='వయస్సు',gender='లింగం',res='నివాసం',occupation='వృత్తి',income='వార్షిక ఆదాయం',category='సామాజిక వర్గం',disability='వికలాంగ స్థితి',language='భాష',requirement='మీకు ఏ సహాయం కావాలి?',findme='నా పథకాలను కనుగొనండి',results='మీ కోసం సిఫార్సు చేసిన పథకాలు',details='వివరాలు చూడండి',benefits='ప్రయోజనాలు',eligibility='అర్హత',documents='అవసరమైన పత్రాలు',application='ఎలా దరఖాస్తు చేయాలి',about='పథకం గురించి',save='సేవ్',logout='లాగ్ అవుట్',ask='AIని అడగండి',next='తర్వాత',back='వెనుకకు')}
for x in LANGS:
    if x not in L:L[x]=L['English']

def db(): return sqlite3.connect(DB)
def init():
    c=db(); c.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,mobile TEXT UNIQUE,email TEXT,age INTEGER,gender TEXT,state TEXT,district TEXT,residence TEXT,occupation TEXT,income TEXT,category TEXT,disability TEXT,language TEXT,password_hash TEXT,salt TEXT)'''); c.execute('''CREATE TABLE IF NOT EXISTS saved(user_id INTEGER,scheme_name TEXT,UNIQUE(user_id,scheme_name))'''); c.commit(); c.close()
def hp(p,s=None):
    s=s or secrets.token_hex(16); return hashlib.pbkdf2_hmac('sha256',p.encode(),s.encode(),120000).hex(),s
def row(m):
    c=db(); r=c.execute('SELECT * FROM users WHERE mobile=?',(m,)).fetchone(); c.close(); return r
def ud(r): return {'id':r[0],'name':r[1],'mobile':r[2],'email':r[3],'age':r[4],'gender':r[5],'state':r[6],'district':r[7],'residence':r[8],'occupation':r[9],'income':r[10],'category':r[11],'disability':r[12],'language':r[13]}
def save_user(d,p):
    h,s=hp(p); c=db()
    try:c.execute('INSERT INTO users(name,mobile,email,age,gender,state,district,residence,occupation,income,category,disability,language,password_hash,salt) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(d['name'],d['mobile'],d['email'],d['age'],d['gender'],d['state'],d['district'],d['residence'],d['occupation'],d['income'],d['category'],d['disability'],d['language'],h,s));c.commit();return True
    except sqlite3.IntegrityError:return False
    finally:c.close()
def auth(m,p):
    r=row(m)
    if not r or not r[14]:return None
    h,_=hp(p,r[15]); return ud(r) if secrets.compare_digest(h,r[14]) else None
def setpw(m,p):
    h,s=hp(p);c=db();c.execute('UPDATE users SET password_hash=?,salt=? WHERE mobile=?',(h,s,m));c.commit();c.close()
def saved(uid):
    c=db();r=c.execute('SELECT scheme_name FROM saved WHERE user_id=?',(uid,)).fetchall();c.close();return {x[0] for x in r}
def toggle(uid,n):
    c=db();r=c.execute('SELECT 1 FROM saved WHERE user_id=? AND scheme_name=?',(uid,n)).fetchone()
    if r:c.execute('DELETE FROM saved WHERE user_id=? AND scheme_name=?',(uid,n));v=False
    else:c.execute('INSERT OR IGNORE INTO saved VALUES(?,?)',(uid,n));v=True
    c.commit();c.close();return v
init()

for k,v in {'user':None,'lang':'English','reg':{},'reg_step':'mobile','reg_verified':False,'forgot_mobile':None,'forgot_verified':False,'access_font':'Medium','high_contrast':False,'large_cursor':False,'results':None,'detail':None,'page':'home'}.items():st.session_state.setdefault(k,v)

def normalize_mobile(m):
    m=re.sub(r'\s+','',m.strip())
    if re.fullmatch(r'\+91[6-9]\d{9}',m): return m
    if re.fullmatch(r'[6-9]\d{9}',m): return '+91'+m
    return None

def sms_ready():
    return Client is not None and all(os.getenv(x) for x in ['TWILIO_ACCOUNT_SID','TWILIO_AUTH_TOKEN','TWILIO_VERIFY_SERVICE_SID'])

def send_sms_otp(m,purpose='signup'):
    key=f'{purpose}:{m}'
    now=time.time()
    meta=st.session_state.setdefault('otp_meta',{})
    previous=meta.get(key,{})
    if now-previous.get('sent_at',0)<30:
        return False,'Please wait 30 seconds before requesting another OTP.'
    if not sms_ready():
        code=str(secrets.randbelow(900000)+100000)
        st.session_state.setdefault('demo_otp_codes',{})[key]=code
        meta[key]={'sent_at':now,'expires_at':now+600,'attempts':0}
        msg='OTP sent (demo mode).'
        if os.getenv('DEMO_MODE','').lower() in {'1','true','yes'}: msg+=f' Debug OTP: {code}'
        return True,msg
    try:
        c=Client(os.getenv('TWILIO_ACCOUNT_SID'),os.getenv('TWILIO_AUTH_TOKEN'))
        c.verify.services(os.getenv('TWILIO_VERIFY_SERVICE_SID')).verifications.create(to=m,channel='sms')
        meta[key]={'sent_at':now,'expires_at':now+600,'attempts':0}
        return True,'OTP sent by SMS.'
    except Exception as e:
        return False,f'Could not send SMS OTP: {e}'

def verify_sms(m,code,purpose='signup'):
    key=f'{purpose}:{m}'
    meta=st.session_state.setdefault('otp_meta',{}).get(key)
    if not meta or time.time()>meta.get('expires_at',0): return False,'OTP expired. Request a new OTP.'
    if meta.get('attempts',0)>=5: return False,'Too many attempts. Request a new OTP.'
    meta['attempts']=meta.get('attempts',0)+1
    if not sms_ready():
        expected=st.session_state.setdefault('demo_otp_codes',{}).get(key,'')
        valid=bool(expected) and secrets.compare_digest(expected,code)
        if valid:
            st.session_state.demo_otp_codes.pop(key,None);st.session_state.otp_meta.pop(key,None)
        return valid,('Mobile number verified.' if valid else 'Incorrect demo OTP.')
    try:
        c=Client(os.getenv('TWILIO_ACCOUNT_SID'),os.getenv('TWILIO_AUTH_TOKEN'))
        r=c.verify.services(os.getenv('TWILIO_VERIFY_SERVICE_SID')).verification_checks.create(to=m,code=code)
        valid=r.status=='approved'
        if valid: st.session_state.otp_meta.pop(key,None)
        return valid,('Mobile number verified.' if valid else 'Incorrect or expired OTP.')
    except Exception as e:
        return False,f'OTP verification failed: {e}'

def css():
    fs={'Small':'14px','Medium':'16px','Large':'19px','Extra Large':'23px'}[st.session_state.get('access_font','Medium')]
    st.markdown(f'''<style>
    html,body,[class*="css"]{{font-size:{fs};}}
    .hero{{padding:50px 30px;border-radius:24px;background:linear-gradient(135deg,#063970,#1680d0);color:white;text-align:center;margin-bottom:22px}}
    .hero h1{{font-size:44px}} .card{{padding:20px;border:1px solid #e5e7eb;border-radius:18px;background:#fff;margin:10px 0}}
    .nav{{padding:8px 0;border-bottom:1px solid #ddd;margin-bottom:20px}}
    .otpbox{{padding:18px;border:2px solid #1680d0;border-radius:14px;background:#f5faff;margin:12px 0}}
    .ai-fab{{position:fixed;right:24px;bottom:24px;z-index:9999;background:#063970;color:#fff!important;padding:14px 20px;border-radius:999px;box-shadow:0 5px 18px #0003;font-weight:700;text-decoration:none!important}}
    .ai-fab:hover{{background:#1680d0}}
    @media (max-width:640px){{.ai-fab{{right:14px;bottom:14px;padding:12px 16px}}.hero h1{{font-size:32px}}}}
    </style>''',unsafe_allow_html=True)
css(); t=L[st.session_state.lang]

top_brand,top_controls=st.columns([3,1])
with top_controls:
    st.session_state.lang=st.selectbox('🌐 Language / భాష',LANGS,index=LANGS.index(st.session_state.lang),key='top_lang')
    with st.expander('♿ Accessibility'):
        st.session_state.access_font=st.selectbox('Text size',['Small','Medium','Large','Extra Large'],index=['Small','Medium','Large','Extra Large'].index(st.session_state.access_font),key='top_text_size')
        st.session_state.high_contrast=st.checkbox('High contrast',st.session_state.high_contrast,key='top_high_contrast')
        st.session_state.large_cursor=st.checkbox('Larger cursor',st.session_state.large_cursor,key='top_large_cursor')
    t=L[st.session_state.lang]

# FIRST-TIME / RETURNING AUTH
if st.session_state.user is None:
    st.markdown('<div class="hero"><h1>🇮🇳 GovScheme AI</h1><p>Find • Understand • Apply</p><p>Personalized government-scheme discovery</p></div>',unsafe_allow_html=True)
    login_tab, signup_tab = st.tabs([f'🔐 {t["login"]}',f'📝 {t["create"]}'])

    with login_tab:
        st.subheader('Welcome back 👋')
        m=st.text_input(t['mobile'],key='lm',placeholder='+91XXXXXXXXXX')
        p=st.text_input(t['password'],type='password',key='lp')
        if st.button(t['login'],type='primary',use_container_width=True):
            nm=normalize_mobile(m); u=auth(nm,p) if nm else None
            if u: st.session_state.user=u; st.session_state.lang=u['language']; st.rerun()
            else: st.error('Invalid mobile number or password.')
        if st.button(t['forgot'],use_container_width=True):
            st.session_state.page='forgot'; st.rerun()

    with signup_tab:
        # One continuous signup flow: Mobile -> SMS OTP -> Profile -> Create Account -> automatic login
        if st.session_state.reg_step=='mobile':
            st.subheader('Create your account')
            st.info('Enter your mobile number. A 6-digit OTP will be sent to you by SMS.')
            m=st.text_input(t['mobile'],key='rm',placeholder='+91XXXXXXXXXX')
            if st.button(t['send'],key='send_reg_otp',type='primary',use_container_width=True):
                nm=normalize_mobile(m)
                if not nm: st.error('Enter a valid Indian mobile number, e.g. +919876543210.')
                elif row(nm): st.error('This mobile number is already registered. Please use Login.')
                else:
                    ok,msg=send_sms_otp(nm,'signup')
                    if ok:
                        st.session_state.reg={'mobile':nm}; st.session_state.reg_step='otp'; st.rerun()
                    else: st.error(msg)

        elif st.session_state.reg_step=='otp':
            m=st.session_state.reg['mobile']
            st.markdown(f'<div class="otpbox"><h3>📱 OTP verification</h3><p>We sent a 6-digit OTP by SMS to <b>{m}</b>.</p><p>Enter it here to continue. You do not need to go back to Sign Up.</p></div>',unsafe_allow_html=True)
            x=st.text_input(t['otp'],max_chars=6,key='reg_otp',placeholder='6-digit OTP')
            if st.button(t['verify'],key='verify_reg_otp',type='primary',use_container_width=True):
                ok,msg=verify_sms(m,x.strip(),'signup')
                if ok:
                    st.session_state.reg_verified=True; st.session_state.reg_step='profile'; st.success(msg); st.rerun()
                else: st.error(msg)
            if st.button('🔄 Resend OTP',key='resend_reg_otp'):
                ok,msg=send_sms_otp(m,'signup')
                if ok: st.success(msg)
                else: st.error(msg)

        elif st.session_state.reg_step=='profile' and st.session_state.reg_verified:
            st.success('✅ Mobile verified. Complete your profile below — no need to go back.')
            d=st.session_state.reg
            c1,c2=st.columns(2)
            with c1:
                d['name']=st.text_input(t['name'],key='reg_name'); d['email']=st.text_input(t['email'],key='reg_email')
                d['age']=st.number_input(t['age'],1,120,20,key='reg_age')
                d['gender']=st.selectbox(t['gender'],['Male','Female','Transgender','Prefer not to say'],key='reg_gender')
                d['state']=st.selectbox(t['state'],STATES,key='reg_state'); d['district']=st.text_input(t['district'],key='reg_district')
            with c2:
                d['residence']=st.selectbox(t['res'],['Urban','Rural'],key='reg_res')
                d['occupation']=st.selectbox(t['occupation'],OCC,key='reg_occ'); d['income']=st.selectbox(t['income'],INC,key='reg_inc')
                d['category']=st.selectbox(t['category'],CAT,key='reg_cat')
                d['disability']=st.selectbox(t['disability'],['No','Yes','Prefer not to say'],key='reg_dis')
                d['language']=st.selectbox(t['language'],LANGS,index=LANGS.index(st.session_state.lang),key='reg_lang')
            p1=st.text_input('Set Password',type='password',key='reg_p1'); p2=st.text_input('Confirm Password',type='password',key='reg_p2')
            if st.button('Create Account & Continue',type='primary',use_container_width=True):
                if not d.get('name','').strip(): st.warning('Enter your full name.')
                elif len(p1)<8: st.warning('Password must contain at least 8 characters.')
                elif p1!=p2: st.error('Passwords do not match.')
                elif save_user(d,p1):
                    st.session_state.user=ud(row(d['mobile'])); st.session_state.lang=d['language']
                    st.session_state.reg={}; st.session_state.reg_step='mobile'; st.session_state.reg_verified=False
                    st.session_state.page='home'; st.success('🎉 Account created successfully. You are now logged in.'); st.rerun()
                else: st.error('Could not create account. This mobile may already be registered.')

    if st.session_state.page=='forgot':
        st.divider(); st.subheader('🔑 '+t['forgot'])
        if not st.session_state.forgot_verified:
            m=st.text_input(t['mobile'],key='fm',placeholder='+91XXXXXXXXXX')
            if st.button(t['send'],key='fs',type='primary'):
                nm=normalize_mobile(m)
                if not nm: st.error('Enter a valid Indian mobile number.')
                elif not row(nm): st.error('No account found.')
                else:
                    ok,msg=send_sms_otp(nm,'forgot')
                    if ok: st.session_state.forgot_mobile=nm; st.session_state.page='forgot_otp'; st.rerun()
                    else: st.error(msg)
        else:
            p1=st.text_input('New Password',type='password',key='fp1'); p2=st.text_input('Confirm New Password',type='password',key='fp2')
            if st.button('Reset Password',type='primary'):
                if len(p1)>=8 and p1==p2:
                    setpw(st.session_state.forgot_mobile,p1); st.success('Password reset successfully. You can now log in.')
                    st.session_state.forgot_mobile=None; st.session_state.forgot_verified=False; st.session_state.page='login'
                else: st.error('Passwords must match and contain at least 8 characters.')
    if st.session_state.page=='forgot_otp':
        st.subheader('📱 Enter OTP sent by SMS')
        x=st.text_input(t['otp'],max_chars=6,key='forgot_otp')
        if st.button(t['verify'],key='fv',type='primary'):
            ok,msg=verify_sms(st.session_state.forgot_mobile,x.strip(),'forgot')
            if ok: st.session_state.forgot_verified=True; st.session_state.page='forgot'; st.success(msg); st.rerun()
            else: st.error(msg)
    st.stop()

# LOAD MODEL
@st.cache_resource
def model():return joblib.load('scheme_recommendation_model.pkl'),joblib.load('scheme_tfidf_matrix.pkl'),joblib.load('government_schemes_data.pkl')
try:vec,mat,df=model();df=df if isinstance(df,pd.DataFrame) else pd.DataFrame(df)
except Exception as e:st.error('Model files could not be loaded.');st.code(str(e));st.stop()

u=st.session_state.user;t=L[st.session_state.lang]
if st.query_params.get('page') in {'home','find','saved','ai'}:
    st.session_state.page=st.query_params.get('page')
    st.query_params.clear()

with st.sidebar:
    st.divider()
    st.markdown('### Navigation')
    if st.button('🏠 '+t['home'],use_container_width=True,key='sidebar_home'):
        st.session_state.page='home'
    if st.button('❤️ '+t['saved'],use_container_width=True,key='sidebar_saved'):
        st.session_state.page='saved'
    if st.button('👤 '+t['profile'],use_container_width=True,key='sidebar_profile'):
        st.session_state.page='profile'
    st.divider()
    st.markdown('### 👤 Customer details')
    st.write(f'**{t["name"]}:** {u["name"]}')
    st.write(f'**{t["mobile"]}:** {u["mobile"]}')
    st.write(f'**{t["state"]}:** {u["state"]}')
    st.write(f'**{t["occupation"]}:** {u["occupation"]}')
    if st.button('🚪 '+t['logout'],use_container_width=True,key='sidebar_logout'):
        st.session_state.user=None;st.rerun()

# NAV
st.markdown(f'<div class="nav"><h2>🇮🇳 GovScheme AI</h2><p>👋 {html.escape(str(u["name"]))} &nbsp; | &nbsp; {html.escape(str(u["state"]))}</p></div>',unsafe_allow_html=True)
_,find_nav,_=st.columns([1,1.3,1])
if find_nav.button('🔎 '+t['find'],type='primary',use_container_width=True):
    st.session_state.page='find'

# HOME
if st.session_state.page=='home':
    st.markdown('<div class="hero"><h1>Find Government Schemes For You</h1><p>Discover schemes based on your profile and needs.</p></div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    for col,title,text in [(a,'① Enter Details','Use your profile and tell us what you need.'),(b,'② Find Schemes','Our existing recommendation model ranks relevant schemes.'),(c,'③ Select & Apply','Read eligibility, benefits, documents and application information.')]:
        with col:st.markdown(f'<div class="card"><h3>{title}</h3><p>{text}</p></div>',unsafe_allow_html=True)
    st.subheader('Explore Government Schemes')
    tab1,tab2,tab3=st.tabs(['📂 Categories','🗺️ States / UTs','🏛️ Central Ministries'])
    with tab1:
        cols=st.columns(3)
        for i,(cat,count) in enumerate(CATEGORY_COUNTS.items()):
            cols[i%3].markdown(f'<div class="card"><h4>{cat}</h4><p><b>{count:,}</b> schemes</p></div>',unsafe_allow_html=True)
    with tab2:
        cols=st.columns(3)
        for i,state in enumerate(STATES):
            cols[i%3].button(state,use_container_width=True,key='state_dir'+str(i))
    with tab3:
        cols=st.columns(2)
        for i,ministry in enumerate(MINISTRIES):
            cols[i%2].button(ministry,use_container_width=True,key='min_dir'+str(i))
    if st.button('🎯 '+t['findme'],type='primary',use_container_width=True):st.session_state.page='find';st.rerun()

# FIND
if st.session_state.page=='find':
    st.header('🔎 '+t['find']);st.progress(1.0,text='Step 1 — Enter your requirement')
    q=st.text_area(t['requirement'],placeholder='Example: I am a student looking for scholarship support for higher education.',height=130)
    c1,c2,c3=st.columns(3)
    with c1:s=st.selectbox(t['state'],STATES,index=STATES.index(u['state']) if u['state'] in STATES else 0);occ=st.selectbox(t['occupation'],OCC,index=OCC.index(u['occupation']) if u['occupation'] in OCC else 0)
    with c2:inc=st.selectbox(t['income'],INC,index=INC.index(u['income']) if u['income'] in INC else 0);cat=st.selectbox(t['category'],CAT,index=CAT.index(u['category']) if u['category'] in CAT else 0)
    with c3:res=st.selectbox(t['res'],['Urban','Rural'],index=['Urban','Rural'].index(u['residence']) if u['residence'] in ['Urban','Rural'] else 0);age=st.number_input(t['age'],1,120,(lambda v: v if isinstance(v,int) and 1<=v<=120 else 20)(u['age']))
    category_filter=st.selectbox('Scheme Category (optional)',['All Categories']+list(CATEGORY_COUNTS.keys()))
    if st.button('🎯 '+t['findme'],type='primary',use_container_width=True):
        if not q.strip():st.warning('Please describe your requirement.')
        else:
            text=f'State {s}; Age {age}; Occupation {occ}; Income {inc}; Category {cat}; Residence {res}; Requirement {q}'
            scores=cosine_similarity(vec.transform([text]),mat).flatten()
            eligible=np.arange(len(df))
            if category_filter!='All Categories' and 'schemeCategory' in df.columns:
                mask=df['schemeCategory'].astype(str).str.strip().eq(category_filter)
                eligible=np.flatnonzero(mask.to_numpy())
            if len(eligible)==0:
                st.warning('No schemes in this category. Try another category.')
            else:
                ranked=eligible[np.argsort(scores[eligible])[-min(8,len(eligible)):][::-1]]
                st.session_state.results=(df.iloc[ranked].copy(),scores[ranked]);st.session_state.page='results';st.rerun()

# RESULTS
if st.session_state.page=='results' and st.session_state.results:
    r,sc=st.session_state.results;st.header('🎯 '+t['results']);ss=saved(u['id'])
    for i,(_,x) in enumerate(r.iterrows()):
        name=str(x.get('scheme_name','Government Scheme'));score=round(float(sc[i])*100,2)
        st.markdown('<div class="card">',unsafe_allow_html=True);st.subheader(name)
        a,b,c,d=st.columns(4);a.metric('Match',f'{score}%');b.write('**Category**');b.write(x.get('schemeCategory','Not specified'));c.write('**Level**');c.write(x.get('level','Not specified'))
        if d.button('❤️ Saved' if name in ss else '♡ Save',key='sv'+str(i)):toggle(u['id'],name);st.rerun()
        if st.button('📋 '+t['details'],key='dt'+str(i),use_container_width=True):st.session_state.detail=(x.to_dict(),score);st.session_state.page='detail';st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# DETAILS
if st.session_state.page=='detail' and st.session_state.detail:
    x,score=st.session_state.detail;st.button('← Back',on_click=lambda:st.session_state.update(page='results',detail=None));st.header(x.get('scheme_name','Government Scheme'));st.metric('Your Match Score',f'{score}%')
    st.write('**Category:**',x.get('schemeCategory','Not specified'));st.write('**Government Level:**',x.get('level','Not specified'));st.divider()
    for key,label in [('details',t['about']),('benefits',t['benefits']),('eligibility',t['eligibility']),('documents',t['documents']),('application',t['application'])]:st.subheader(label);st.write(x.get(key,'Not available.'))
    if st.button('❤️ '+t['save']):toggle(u['id'],str(x.get('scheme_name','')));st.toast('Saved')
    st.info('Verify current eligibility and application details with the relevant official government authority before applying.')

# SAVED
if st.session_state.page=='saved':
    st.header('❤️ '+t['saved']);names=saved(u['id'])
    if not names:st.info('No saved schemes yet.')
    for name in names:
        x=df[df['scheme_name'].astype(str)==name]
        if not x.empty:
            r=x.iloc[0];st.markdown('<div class="card">',unsafe_allow_html=True);st.subheader(name);st.write(r.get('schemeCategory',''));st.write(r.get('details','Not available.'));st.markdown('</div>',unsafe_allow_html=True)

# PROFILE
if st.session_state.page=='profile':
    st.header('👤 '+t['profile']);a,b=st.columns(2)
    for col,pairs in [(a,[('name',t['name']),('mobile',t['mobile']),('email',t['email']),('age',t['age']),('gender',t['gender'])]),(b,[('state',t['state']),('district',t['district']),('residence',t['res']),('occupation',t['occupation']),('income',t['income']),('category',t['category'])])]:
        for k,lbl in pairs:col.write(f'**{lbl}:** {u[k]}')
    st.divider();st.subheader('Change Password');old=st.text_input('Current Password',type='password');p1=st.text_input('New Password',type='password');p2=st.text_input('Confirm New Password',type='password')
    if st.button('Update Password'):
        if auth(u['mobile'],old) and len(p1)>=8 and p1==p2:
            setpw(u['mobile'],p1);st.session_state.user=ud(row(u['mobile']));u=st.session_state.user;st.success('Password updated.')
        else:st.error('Current password is wrong or new passwords are invalid.')

# AI
if st.session_state.page=='ai':
    st.header('🤖 '+t['ai']);q=st.text_area('Ask your question',placeholder='Which scheme is best for me? What documents do I need?')
    if st.button('💬 '+t['ask'],type='primary',use_container_width=True):
        if not st.session_state.results:st.warning('Find schemes first.')
        elif not q.strip():st.warning('Enter a question.')
        else:
            r,sc=st.session_state.results;ctx='\n'.join([f"{x.get('scheme_name','')} | Benefits: {x.get('benefits','')} | Eligibility: {x.get('eligibility','')} | Documents: {x.get('documents','')} | Application: {x.get('application','')}" for _,x in r.iterrows()]);key=os.getenv('GEMINI_API_KEY','')
            if key:
                try:
                    from google import genai
                    ans=genai.Client(api_key=key).models.generate_content(model='gemini-2.5-flash',contents=f'You are GovScheme AI. Answer in {st.session_state.lang}. Use only this context; never invent facts. User: {q}\nContext:\n{ctx}').text;st.success(ans)
                except Exception as e:st.error('AI service failed.');st.code(str(e))
            else:
                ql=q.lower()
                if 'document' in ql:
                    for _,x in r.iterrows():st.markdown(f"**{x.get('scheme_name','Scheme')}**");st.write(x.get('documents','Not available.'))
                elif 'benefit' in ql or 'amount' in ql:
                    for _,x in r.iterrows():st.markdown(f"**{x.get('scheme_name','Scheme')}**");st.write(x.get('benefits','Not available.'))
                elif 'eligib' in ql:
                    for _,x in r.iterrows():st.markdown(f"**{x.get('scheme_name','Scheme')}**");st.write(x.get('eligibility','Not available.'))
                else:st.info(f"Strongest match: {r.iloc[0].get('scheme_name','Scheme')} ({round(float(sc[0])*100,2)}%). Configure GEMINI_API_KEY for conversational AI.")

st.markdown('<a class="ai-fab" href="/?page=ai">🤖 AI Assistant</a>',unsafe_allow_html=True)

st.divider();st.caption('GovScheme AI is a recommendation assistant. Match scores are not official eligibility decisions. Verify current government information before applying.')
