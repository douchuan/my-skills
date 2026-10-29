请根据 [示例剧本]，把 [文章] 转换为 [剧本]

## 示例剧本

```yaml
title: Dream of the Red Chamber - Sample Scene

tts:
  provider: qwen
  model: qwen-audio-3.1-tts-flash
  region: cn-beijing
  format: mp3
  sample_rate: 24000

output_dir: output/dream-of-red-chamber

characters:
  narrator:
    name: Narrator
    voice: longanhuan_v3.1
  baoyu:
    name: Jia Baoyu
    voice: longanhuan_v3.1
  daiyu:
    name: Lin Daiyu
    voice: longanlingxin_v3.1

segments:
  - id: opening
    speaker: narrator
    emotion: neutral 
    rate: 0.95
    text: "潇湘馆内，竹影摇曳，林黛玉正倚窗读书。"
    pause_after: 0.8

  - id: baoyu-greeting
    speaker: baoyu
    emotion: gentle
    rate: 1.0
    text: "妹妹今日气色倒好些了。"
    pause_after: 0.4

  - id: daiyu-reply
    speaker: daiyu
    emotion: curious
    rate: 0.95
    text: "你又来打趣我。今日怎么有空过来？"
    pause_after: 0.6

  - id: narrator-close
    speaker: narrator
    emotion: neutral
    rate: 0.95
    text: "宝玉笑着坐下，窗外传来一阵清脆的鸟鸣。"
```
## 支持的 emotion

```py
_EMOTION_INSTRUCTIONS = {
    # 1. 基础情绪
    "neutral": "Speak naturally and clearly, with a balanced, neutral tone.",
    # 2. 温暖与亲和
    "gentle": "Speak gently and warmly, with a soft and reassuring tone.",
    "empathetic": "Speak with warmth, compassion, and genuine understanding.",
    "tender": "Speak with soft affection and delicate care.",
    "grateful": "Speak with sincere gratitude and heartfelt appreciation.",
    # 3. 快乐与积极
    "cheerful": "Speak brightly and cheerfully, with a light, upbeat tone.",
    "excited": "Speak with energetic excitement and enthusiasm.",
    "hopeful": "Speak with optimism and confidence in a positive outcome.",
    "playful": "Speak in a lighthearted, mischievous, and teasing manner.",
    # 4. 悲伤与失落
    "sad": "Speak sadly, with restrained emotion and a subdued voice.",
    "mournful": "Speak with profound grief, as if mourning a great loss.",
    "melancholy": "Speak with quiet, reflective sadness and wistful longing.",
    "disappointed": "Speak with subdued disappointment and unmet expectations.",
    # 5. 愤怒与对抗
    "annoyed": "Speak with irritation and restrained impatience.",
    "angry": "Speak angrily, with sharp emphasis and strong emotional intensity.",
    "furious": "Speak with explosive rage and barely contained anger.",
    "scornful": "Speak with contempt and disdain.",
    "sarcastic": "Speak with biting irony and a mocking, sarcastic undertone.",
    # 6. 恐惧与紧张
    "anxious": "Speak with nervous worry and apprehension.",
    "frightened": "Speak with clear fear and dread, with a slightly shaky voice.",
    "panicked": "Speak rapidly and breathlessly, conveying intense panic and alarm.",
    "tense": "Speak in a tight, strained voice, conveying pressure and suspense.",
    # 7. 惊讶与思考
    "surprised": "Speak with a sudden lift in tone, as if caught off guard.",
    "amazed": "Speak with astonishment and wonder at something extraordinary.",
    "curious": "Speak with genuine curiosity and an inquisitive tone.",
    "thoughtful": "Speak reflectively and pensively, as if carefully considering an idea.",
    # 8. 严肃与坚定
    "serious": "Speak in a serious, composed, and measured manner.",
    "resolute": "Speak with firm determination and unwavering resolve.",
    "authoritative": "Speak with calm authority, confidence, and control.",
    # 9. 疲惫与冷淡
    "weary": "Speak with low energy and deep physical or emotional fatigue.",
    "indifferent": "Speak in a flat, emotionally detached tone, with little concern.",
    # 10. 神秘与戏剧性
    "mysterious": "Speak in a low, enigmatic tone, creating a sense of mystery.",
}
```

## 文章

```txt

```

## 注意事项

- narrator 是一个中性角色，不包含任何情感, emotion 通常为 neutral

