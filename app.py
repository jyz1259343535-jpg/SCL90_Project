import streamlit as st
from openai import OpenAI
import os

# ================= 1. 核心配置 =================

# 🔴 必填：你的 DeepSeek API Key (发布前一定要确认这里填了！)
DEEPSEEK_API_KEY = "sk-be0e9b008e8049a28b5e6bfbe4243736"

# 🔴 代理配置 (部署到云端时，云端通常不需要代理，这两行可以保留，不影响)
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:8086"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8086"

# 卡密库 (模拟)
VALID_TOKENS = ["jjyyzz202"] 

# ================= 2. 页面配置 =================
st.set_page_config(
    page_title="InnerPeace · 深度心理", 
    page_icon="🌿", 
    layout="centered"
)

# ================= 3. CSS 样式 (Ins风) =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans SC', sans-serif;
        color: #4A4A4A;
    }
    .stApp {
        background-color: #FFFBF0; 
        background-image: radial-gradient(#E8E6E1 1px, transparent 0);
        background-size: 20px 20px;
    }
    header, footer, #MainMenu {visibility: hidden;}

    /* 输入框 */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #333333 !important;
        border: 2px solid #D6CCC2 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    
    /* 进度条 */
    .stProgress > div > div > div > div {
        background-color: #A3B18A;
        border-radius: 10px;
    }

    /* 通用卡片 */
    .ins-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(163, 177, 138, 0.1);
        margin-bottom: 20px;
        border: 1px solid #F0F0F0;
    }
    
    /* 引导语卡片 (新功能) */
    .intro-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAF9F6 100%);
        padding: 25px;
        border-radius: 20px;
        border: 1px dashed #A3B18A;
        margin-bottom: 25px;
        text-align: center;
    }

    /* 按钮 */
    .stButton > button {
        border-radius: 50px !important;
        height: 50px;
        font-weight: 600;
        border: none;
    }
    .primary-btn button {
        background: linear-gradient(135deg, #A3B18A 0%, #588157 100%) !important;
        color: white !important;
    }
    .secondary-btn button {
        background-color: #E5E5E5 !important;
        color: #333333 !important;
    }
    .nav-btn button {
        background-color: white !important;
        border: 1px solid #A3B18A !important;
        color: #588157 !important;
        font-size: 12px !important;
        padding: 0px !important;
        height: 35px !important;
    }

    /* 结果页 */
    .factor-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px dashed #E5E7EB;
        color: #333;
    }
    .tag {padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: bold;}
    .tag-green {background: #E9F5E9; color: #2E7D32;}
    .tag-yellow {background: #FFF8E1; color: #F57F17;}
    .tag-red {background: #FFEBEE; color: #C62828;}
</style>
""", unsafe_allow_html=True)

# ================= 4. 数据核心 =================

if 'page' not in st.session_state: st.session_state.page = 'login'
if 'current_q' not in st.session_state: st.session_state.current_q = 1
if 'answers' not in st.session_state: st.session_state.answers = {}

factors_map = {
    "躯体化": [1, 4, 12, 27, 40, 42, 48, 49, 52, 53, 56, 58],
    "强迫症状": [3, 9, 10, 28, 38, 45, 46, 51, 55, 65],
    "人际关系敏感": [6, 21, 34, 36, 37, 41, 61, 69, 73],
    "抑郁": [5, 14, 15, 20, 22, 26, 29, 30, 31, 32, 54, 71, 79],
    "焦虑": [2, 17, 23, 33, 39, 57, 72, 78, 80, 86],
    "敌对": [11, 24, 63, 67, 74, 81],
    "恐怖": [13, 25, 47, 50, 70, 75, 82],
    "偏执": [8, 18, 43, 68, 76, 83],
    "精神病性": [7, 16, 35, 62, 77, 84, 85, 87, 88, 90],
    "其他": [19, 44, 59, 60, 64, 66, 89]
}

questions_db = {
    1: "头痛", 2: "神经过敏，心中不踏实", 3: "头脑中有不必要的想法或字句盘旋", 4: "头昏或昏倒", 5: "对异性的兴趣减退",
    6: "对旁人责备求全", 7: "感到别人能控制您的思想", 8: "责怪别人制造麻烦", 9: "忘性大", 10: "担心自己的衣饰整齐及仪态的端正",
    11: "容易烦恼和激动", 12: "胸痛", 13: "害怕空旷的场所或街道", 14: "感到自己的精力下降，活动减慢", 15: "想结束自己的生命",
    16: "听到旁人听不到的声音", 17: "发抖", 18: "感到大多数人都不可信任", 19: "胃口不好", 20: "容易哭泣",
    21: "同异性相处时感到害羞不自在", 22: "感到受骗，中了圈套或有人想抓住您", 23: "无缘无故地突然感到害怕", 24: "自己不能控制地发脾气", 25: "怕单独出门",
    26: "经常责怪自己", 27: "腰痛", 28: "感到难以完成任务", 29: "感到孤独", 30: "感到苦闷",
    31: "过分担忧", 32: "对事物不感兴趣", 33: "感到害怕", 34: "您的感情容易受到伤害", 35: "旁人能知道您的私下想法",
    36: "感到别人不理解您、不同情您", 37: "感到人们对您不友好，不喜欢您", 38: "做事必须做得很慢以保证做得正确", 39: "心跳得很厉害", 40: "恶心或胃部不舒服",
    41: "感到比不上别人", 42: "肌肉酸痛", 43: "感到有人在监视您、谈论您", 44: "难以入睡", 45: "做事必须反复检查",
    46: "难以作出决定", 47: "怕乘电车、公共汽车、地铁或火车", 48: "呼吸有困难", 49: "一阵阵发冷或发热", 50: "因为感到害怕而避开某些东西、场合或活动",
    51: "脑子变空了", 52: "身体发麻或刺痛", 53: "喉咙有梗塞感", 54: "感到没有前途没有希望", 55: "不能集中注意力",
    56: "身体某一部分软弱无力", 57: "感到紧张或容易紧张", 58: "感到手或脚发重", 59: "想到死亡的事", 60: "吃得太多",
    61: "当别人看着您或谈论您时感到不自在", 62: "有一些不属于您自己的想法", 63: "有想打人或伤害他人的冲动", 64: "醒得太早", 65: "必须反复洗手、点数目或触摸某些东西",
    66: "睡得不稳不深", 67: "有想摔坏或破坏东西的冲动", 68: "有别人没有的想法", 69: "感到对别人神经过敏", 70: "在商店或电影院等人多的地方感到不自在",
    71: "感到任何事情都很困难", 72: "一阵阵恐惧或惊恐", 73: "感到在公共场合吃东西很不舒服", 74: "经常与人争论", 75: "单独一人时神经很紧张",
    76: "别人对您的成绩没有作出恰当的评价", 77: "即使和别人在一起也感到孤单", 78: "感到坐立不安", 79: "感到自己没有价值", 80: "感到熟悉的东西变成陌生或不像是真的",
    81: "大叫或摔东西", 82: "害怕要在公共场合昏倒", 83: "感到别人想占您的便宜", 84: "为一些有关“性”的想法而很苦恼", 85: "认为自己应该因为自己的过错而受到惩罚",
    86: "感到要赶快把事情做完", 87: "感到自己的身体有严重问题", 88: "从未感到和其他人很亲近", 89: "感到有罪恶感", 90: "认为自己的脑子有毛病"
}

def get_deepseek_report(scores):
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    prompt = f"""
    你是一位治愈系心理咨询师。请根据SCL-90各因子得分进行【逐项深度解析】。
    得分数据：{scores}
    【要求】
    1. 必须包含所有10个因子，不可遗漏。
    2. 若分数 < 2：简短夸奖，标示(✨状态佳)。
    3. 若分数 >= 2：解释该症状含义（去病耻化），并给出2条具体的CBT行动建议，标示(⚠️需呵护)或(🚨需重视)。
    4. 输出Markdown格式，排版清爽。
请务必要充满人情味、要有专业性，每个因子的深度解析字数一定不能少，能多就多。
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", messages=[{"role": "user", "content": prompt}], stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return "✨ 治愈信件生成中...AI正在连接云端..."

# ================= 5. 页面逻辑 =================

# --- A. 登录页 (含新增的欢迎语) ---
if st.session_state.page == 'login':
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: #5F6F52; font-weight: 300; margin-bottom:5px;">INNER PEACE</h1>
        <p style="color: #A3B18A; letter-spacing: 2px;">探索 · 治愈 · 成长</p>
    </div>
    """, unsafe_allow_html=True)
    
    # === ✨ 新增：欢迎引导卡片 ===
    st.markdown("""
    <div style="max-width: 400px; margin: 20px auto;">
        <div class="intro-card">
            <h4 style="color: #5F6F52; margin: 0 0 10px 0;">👋 你好，这里是 Inner Peace</h4>
            <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 15px;">
                这是一份基于 <strong>SCL-90 国际通用量表</strong> 的深度心理探索。<br>
                我们将从 10 个维度，为你绘制一份专属的心灵画像。
            </p>
            <div style="background-color: #F0F4E8; padding: 10px; border-radius: 10px; font-size: 13px; color: #588157;">
                ⏳ <strong>测评耗时：</strong> 约 5-8 分钟<br>
                💡 <strong>提示：</strong> 请凭第一直觉回答，答案无对错
            </div>
            <p style="font-size: 12px; color: #999; margin-top: 15px;">
                请在安静的环境下，深呼吸，领取你的专属诊断报告 👇
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ===============================

    st.markdown("<div class='ins-card' style='max-width: 400px; margin: 0 auto;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:14px; color:#888;'>请输入您的专属通行证</p>", unsafe_allow_html=True)
    
    token = st.text_input("Token", label_visibility="collapsed", placeholder="输入卡密 (如 VIP888)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("开启旅程 →"):
            if token in VALID_TOKENS:
                st.session_state.page = 'test'
                st.rerun()
            else:
                st.error("通行证无效")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- B. 答题页 ---
elif st.session_state.page == 'test':
    st.progress(st.session_state.current_q / 90)
    q_id = st.session_state.current_q
    
    st.markdown(f"""
    <div class="ins-card" style="min-height: 220px; display:flex; flex-direction:column; justify-content:center;">
        <div style="color:#A3B18A; font-size:14px; text-align:center; margin-bottom:15px;">QUESTION {q_id} / 90</div>
        <div style="font-size: 20px; font-weight: 500; color: #333; text-align: center; line-height: 1.6;">
            {questions_db.get(q_id, "题目加载中...")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 选项交互
    st.markdown("<div style='padding: 0 10px;'>", unsafe_allow_html=True)
    val_map = {"从无":1, "轻度":2, "中度":3, "偏重":4, "严重":5}
    default_val = "从无"
    for k, v in val_map.items():
        if st.session_state.answers.get(q_id) == v: default_val = k
            
    answer = st.select_slider("你的真实感受：", options=["从无", "轻度", "中度", "偏重", "严重"], value=default_val)
    st.session_state.answers[q_id] = val_map[answer]
    st.markdown("</div><br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("← 上一题") and q_id > 1:
            st.session_state.current_q -= 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if q_id < 90:
            if st.button("下一题 →"):
                st.session_state.current_q += 1
                st.rerun()
        else:
            if st.button("生成报告 ✨"):
                for i in range(1, 91):
                     if i not in st.session_state.answers: st.session_state.answers[i] = 1
                st.session_state.page = 'report'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 导航
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🧩 查看做题进度 (点击跳转)", expanded=False):
        st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
        cols = st.columns(10)
        for i in range(1, 91):
            is_done = i in st.session_state.answers
            label = f"{i}✅" if is_done else f"{i}"
            if cols[(i-1)%10].button(label, key=f"nav_{i}"):
                st.session_state.current_q = i
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- C. 报告页 ---
elif st.session_state.page == 'report':
    scores = {}
    for k, v in factors_map.items():
        scores[k] = round(sum([st.session_state.answers.get(i,1) for i in v])/len(v), 2)
    total = sum(st.session_state.answers.values())

    st.markdown(f"""
    <div class="ins-card" style="text-align:center; background: linear-gradient(135deg, #FFFFFF 0%, #FDFCF0 100%);">
        <h3 style="color:#5F6F52; margin-bottom:20px;">您的心灵状态画像</h3>
        <div style="width: 100px; height: 100px; border-radius: 50%; background: #FEFAE0; border: 4px solid #DDA15E; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; color: #BC6C25; margin: 0 auto;">
            {total}
        </div>
        <p style="color:#A3B18A; margin-top:10px; font-size:14px;">SCL-90 总分</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📊 因子概览")
    st.markdown('<div class="ins-card">', unsafe_allow_html=True)
    for k, v in scores.items():
        if v < 2: tag_class, tag_text = "tag-green", "✨ 状态佳"
        elif v < 3: tag_class, tag_text = "tag-yellow", "⚠️ 轻度"
        else: tag_class, tag_text = "tag-red", "🚨 重视"
        st.markdown(f"""
        <div class="factor-row">
            <span style="font-weight:500;">{k}</span>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-weight:bold; color:#5F6F52;">{v}</span>
                <span class="tag {tag_class}">{tag_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 💌 深度治愈指南")
    if 'deep_report' not in st.session_state:
        with st.spinner("小静正在用心解读您的每一项数据..."):
            st.session_state.deep_report = get_deepseek_report(scores)
    
    st.markdown(f"""
    <div class="ins-card" style="line-height: 1.8; color: #333;">
        {st.session_state.deep_report}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="background-color: #E5E7EB; padding: 15px; border-radius: 10px; font-size: 12px; color: #666;">
        <strong>ℹ️ 关于结果的说明 (Disclaimer)：</strong><br>
        本测评结果仅供心理健康自我探索参考，<strong>不具备医疗诊断效力</strong>。
    </div>
    """, unsafe_allow_html=True)