#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_comment.py — 生成 comment.md（虚拟观众弹幕 JSON，200 条）。

  gen_comment.py --out <pkg>/comment.md --lang en
  gen_comment.py --out <pkg>/comment.md --lang ar --lines /tmp/my_lines.txt

约定（铁律）：
  - 恰好 200 条（可用 --count 调整）
  - 键只能是 {nickname, user_url, content}
  - 绝不包含 reply 字段
  - 昵称唯一

--lines 给的是「观众会说的话」一行一条（30-60 条最佳，脚本循环补足 200）。
不给 --lines 时用内置语料池（en / zh / pt / ar）；其他语种请务必自己写 --lines。
"""
import argparse
import json
import os
import random

# ---------------- 昵称生成 ----------------
BASES = [
    "maya", "devon", "priya", "sam", "noah", "rae", "jordan", "casey", "tara", "finn",
    "quinn", "alex", "rio", "ming", "leo", "zoe", "kai", "luca", "nina", "omar",
    "sara", "eli", "jonah", "mira", "theo", "ivy", "max", "lila", "arjun", "hana",
    "chloe", "reza", "yuki", "dani", "cleo", "oscar", "nadia", "felix", "iris", "bram",
    "tess", "marco", "ines", "kofi", "lena", "rudy", "amara", "soren", "pia", "jun",
    "wren", "elias", "niamh", "tariq", "esme", "bo", "cyrus", "yara", "otto", "freya",
    "remy", "anaya", "sol", "kit", "nox", "vega", "indra", "bex", "dax", "lou",
    "sage", "emi", "rune", "joss", "kam", "nell", "ari", "zed", "tova", "jules",
    "lark", "moss", "ash", "baya", "cove", "dune", "echo", "fable", "gale", "hollis",
    "ida", "juno", "kelp", "lume", "mint", "nova", "opal", "pike", "quill", "rue",
    "sable", "tide", "umber", "vale", "wisp", "xan", "yew", "zephyr", "breeze", "cinder",
    "delta", "ember", "flint", "grove", "harbor", "inlet", "jasper", "kestrel", "linden", "mesa",
    "nectar", "orchid", "pebble", "quartz", "ridge", "summit", "thistle", "umber2", "verve", "willow",
]
SUFFIXES = ["", "x", "_", "22", "xo", "99", "z", "tv", "_live", "07", "bb", "kk", "_hd", "3"]


def gen_nicknames(n, seed=7):
    rnd = random.Random(seed)
    pool = BASES[:]
    rnd.shuffle(pool)
    out, seen = [], set()
    i = 0
    while len(out) < n:
        b = pool[i % len(pool)]
        s = SUFFIXES[(i // len(pool)) % len(SUFFIXES)]
        cand = b + s
        if cand not in seen:
            seen.add(cand)
            out.append(cand)
        i += 1
        if i > n * 60:  # 兜底，防死循环
            while True:
                cand = "%s%d" % (b, i)
                i += 1
                if cand not in seen:
                    seen.add(cand)
                    out.append(cand)
                    break
    return out


# ---------------- 内置语料池（观众口吻） ----------------
POOLS = {
    "en": [
        "hey! so glad i caught you live tonight",
        "first time here and this is already so cozy",
        "how are you doing today?",
        "wait i needed this today",
        "this is exactly the vibe i wanted",
        "okay but tell us more about that",
        "i've been here since the start, not leaving",
        "can you talk about this again next time?",
        "haha that got me",
        "you always know what to say",
        "new here, hi everyone",
        "what made you start streaming?",
        "i missed the last one, glad im here now",
        "that story hits different",
        "are you taking requests today?",
        "chat is so friendly here",
        "i told my friend about you",
        "been lurking for weeks, finally saying hi",
        "this made my whole day better",
        "what do you think about it though?",
        "can we go deeper on that?",
        "you seem in a good mood today",
        "sending you good energy",
        "i come here to relax after work",
        "stay a bit longer please",
        "that was such a good point",
        "wait what happened next?",
        "i need to hear the rest of this",
        "do you have a favorite topic?",
        "love this little corner of the internet",
        "second time here, i'm hooked",
        "is it just me or is chat extra nice today",
        "you're the reason i opened the app",
        "that answered something ive wondered for ages",
        "okay i'm staying till the end",
        "someone clip that",
        "genuinely laughing out loud here",
        "what should i do in your opinion?",
        "thanks for always being so kind",
        "see you next time for sure",
    ],
    "zh": [
        "来啦来啦，今天终于赶上了",
        "第一次来，这里好舒服",
        "今天状态怎么样呀",
        "我就是需要这个",
        "这个氛围太对了",
        "再多讲一点嘛",
        "从开头就在了，不走",
        "下次能再聊聊这个吗",
        "哈哈这个笑到我了",
        "你总是知道该说什么",
        "新人报道，大家好",
        "你怎么开始做直播的呀",
        "上次错过了，这次总算在",
        "这个故事有点戳我",
        "今天可以点话题吗",
        "这里的弹幕好友好",
        "我已经安利给朋友了",
        "潜水好几周了，今天冒个泡",
        "今天一整天都被治愈了",
        "你自己怎么看呢",
        "能再深入一点吗",
        "你今天心情不错的样子",
        "给你充点正能量",
        "我下班就来这儿放松",
        "再多播一会儿吧",
        "这个点说得太好了",
        "等等，然后呢",
        "我还想听后面的",
        "你有最喜欢的话题吗",
        "好喜欢这个小角落",
        "第二次来，已经上头了",
        "不是我一个人觉得今天特别好吧",
        "我是因为你才打开这个 app 的",
        "这个问题我想好久了",
        "好，我待到最后",
        "这段得录下来",
        "真的笑出声了",
        "换成你会怎么做呀",
        "谢谢你一直这么温柔",
        "下次一定还来",
    ],
    "pt": [
        "oii, que bom que te encontrei ao vivo hoje",
        "primeira vez aqui e ja me sinto em casa",
        "como voce ta hoje?",
        "eu precisava disso hoje",
        "esse clima ta perfeito",
        "conta mais disso ai",
        "to aqui desde o comeco, nao saio",
        "pode falar disso de novo outra vez?",
        "kkkk isso me pegou",
        "voce sempre sabe o que dizer",
        "sou novo aqui, oi gente",
        "como voce comecou a fazer live?",
        "perdi a ultima, dessa vez to aqui",
        "essa historia me tocou",
        "aceita pedido de assunto hoje?",
        "o chat daqui e muito gente boa",
        "ja indiquei voce pra uma amiga",
        "to na moita faz semanas, hoje falei",
        "meu dia ficou melhor",
        "e voce, o que acha?",
        "pode ir mais fundo nisso?",
        "voce parece bem hoje",
        "te mando uma energia boa",
        "venho aqui pra relaxar depois do trabalho",
        "fica mais um pouquinho",
        "esse ponto foi muito bom",
        "pera, e dai?",
        "quero ouvir o resto",
        "qual seu assunto favorito?",
        "amo esse cantinho da internet",
        "segunda vez aqui e ja viciei",
        "nao sou so eu que acho o chat bom hoje",
        "abri o app por sua causa",
        "isso respondeu uma duvida antiga",
        "beleza, fico ate o fim",
        "alguem salva isso",
        "ri alto aqui",
        "o que voce faria no meu lugar?",
        "obrigada por ser sempre assim",
        "ate a proxima com certeza",
    ],
    "ar": [
        "مرحبا! سعيدة اني لحقتك اليوم",
        "اول مرة هنا والمكان مريح جدا",
        "كيف حالك اليوم؟",
        "كنت محتاجة ده النهاردة",
        "الجو هنا حلو جدا",
        "احكيلنا اكتر عن ده",
        "انا هنا من الاول ومش هامشي",
        "ممكن تتكلمي عن ده تاني؟",
        "هههه ضحكتيني",
        "دائما بتعرفي تقولي الصح",
        "انا جديدة هنا اهلا بالجميع",
        "ازاي بداتي البث؟",
        "فاتني اللي فات بس النهاردة موجودة",
        "القصة دي لمستني",
        "ممكن نقترح مواضيع النهاردة؟",
        "الشات هنا لطيف جدا",
        "انا رشحتك لصاحبتي",
        "بتابع من اسابيع والنهاردة سلمت",
        "يومي اتحسن بفضل ده",
        "وانتي ايه رايك؟",
        "ممكن تتعمقي اكتر؟",
        "شكلك مبسوطة النهاردة",
        "بابعتهالك طاقة حلوة",
        "باجي هنا اهدى بعد الشغل",
        "كملي شوية كمان",
        "النقطة دي كانت ممتازة",
        "استني وبعدين؟",
        "عايزة اسمع الباقي",
        "ايه موضوعك المفضل؟",
        "بحب الركن ده من الانترنت",
        "تاني مرة هنا واتعلقت",
        "مش لوحدي اللي شايفة الشات حلو",
        "فتحت التطبيق عشانك",
        "ده جاوب على سؤال قديم",
        "خلاص هقعد للاخر",
        "حد يحفظ ده",
        "ضحكت بصوت عالي",
        "انتي كنتى تعملي ايه؟",
        "شكرا انك دايما لطيفة",
        "اشوفك المرة الجاية اكيد",
    ],
}


def load_lines(path):
    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if not lines:
        raise SystemExit("--lines 文件为空")
    return lines


def main():
    ap = argparse.ArgumentParser(description="生成 comment.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="en", help="en / zh / pt / ar，或任意语种代码（需配 --lines）")
    ap.add_argument("--lines", help="自定义观众弹幕文件，一行一条")
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    if a.lines:
        lines = load_lines(a.lines)
    else:
        key = a.lang.lower()[:2]
        if key not in POOLS:
            raise SystemExit(
                "语种 %s 无内置语料池。请用 --lines 提供 30-60 条该语言的观众弹幕（一行一条）。" % a.lang
            )
        lines = POOLS[key]

    nicks = gen_nicknames(a.count, a.seed)
    rnd = random.Random(a.seed + 1)
    data = []
    for i, nk in enumerate(nicks):
        # 循环取语料，保证覆盖全部语料后再重复
        content = lines[i % len(lines)] if i < len(lines) else lines[rnd.randrange(len(lines))]
        data.append({"nickname": nk, "user_url": "", "content": content})

    # 校验
    assert len(data) == a.count
    assert len({d["nickname"] for d in data}) == a.count, "昵称重复"
    assert all(set(d.keys()) == {"nickname", "user_url", "content"} for d in data), "键集不合规"

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("已生成 %s：%d 条（键仅 nickname/user_url/content，无 reply）" % (a.out, a.count))


if __name__ == "__main__":
    main()
