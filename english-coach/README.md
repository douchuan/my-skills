# English Coach

A Claude Code skill for proofreading English articles and appending a structured review report.

Write your English article in a Markdown file, invoke the skill, and it will check spelling, word choice, and grammar — then suggest more natural, native-sounding alternatives. The full review is appended to the end of the original file, leaving your article untouched.

**Core philosophy: preserve your voice, explain every finding, help you improve with each pass.**

## 功能特性

- **单词与用词校对**：检查拼写错误、单词形式错误以及不恰当的用词。
- **语法检查**：识别语法错误，并用中文解释错误原因和相关规则。
- **地道表达建议**：提供更自然、更符合英语习惯的表达方式，不刻意使用复杂词汇。
- **中文批改注释**：使用中文解释修改原因，英文展示原句、修改结果和示例。
- **原文件追加报告**：将批改意见直接写入原 Markdown 文件末尾。
- **保护原文**：默认不修改原文章，只在末尾增加批改报告。
- **支持重复批改**：再次调用时更新已有报告，避免重复追加。
- **学习总结**：提炼值得关注的语言问题和实用表达，帮助你积累写作经验。

## 环境要求

- 已安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
- 准备好需要校对的 Markdown 文件（`.md`）

## 安装方法

### 1. 创建 Skill 目录

在项目根目录下创建以下目录结构：

```text
your-project/
├── .claude/
│   └── skills/
│       └── english-coach/
│           └── SKILL.md
├── my-article.md
└── README.md
```

### 2. 配置 Skill

将完整的 Skill 定义保存到：

`.claude/skills/english-coach/SKILL.md`

`SKILL.md` 中定义了校对规则、报告格式、文件修改方式和执行流程。

如果希望在所有项目中使用，也可以将 Skill 安装到用户级目录：

`~/.claude/skills/english-coach/SKILL.md`

项目级 Skill 适合仅在当前项目中使用；用户级 Skill 则适合跨项目复用。

## 使用方法

### 1. 准备英文文章

例如，创建 `my-article.md`：

```markdown
# My Thoughts on AI

I think AI will change the way people work.
It can help us solve problems more efficiency.

However, we should also consider the risks of AI.
```

### 2. 调用 Skill

在 Claude Code 中输入：

```text
/english-coach @my-article.md
```

其中：

- `/english-coach`：调用英语校对 Skill。
- `@my-article.md`：指定需要校对的 Markdown 文件。

Claude Code 会读取指定文件，检查文章，并将批改报告写入该文件末尾。

如果文件路径无法解析或文件不可读取，Skill 应提示你检查路径，而不是猜测文件内容。

### 3. 查看批改结果

批改完成后，原文件会保留原有文章，并在末尾增加：

```markdown
---

## English Review

### 1. Spelling and Word Choice

| Original | Correction | Explanation |
|---|---|---|
| more efficiency | more efficiently | 此处修饰动词 solve，应使用副词 efficiently，而不是名词 efficiency。 |

### 2. Grammar

未发现其他明确的语法错误。

### 3. More Natural Expressions

| Original | More Natural Expression | Explanation |
|---|---|---|
| change the way people work | transform how people work | transform 可以更突出改变的程度，但原表达本身也是正确、自然的。 |

### 4. Learning Summary

**Key Takeaways**

- 注意区分形容词、副词和名词。
- 选择表达时，要考虑语境和实际含义。

**Useful Expression**

- solve problems efficiently：高效地解决问题。
- Example: AI can help us solve problems efficiently.

**Overall Feedback**

文章结构清晰，意思表达明确。接下来可以重点关注词性和修饰关系。
```

以上内容仅用于展示报告格式，实际批改结果以文章内容为准。

## 批改报告说明

每次批改包含四个部分。

### 1. Spelling and Word Choice（拼写与用词）

检查单词拼写、词形以及上下文中的用词是否正确。

例如：

| 原文 | 修改建议 | 中文说明 |
|---|---|---|
| make a research | conduct research | 英语中通常使用 conduct research 或 do research。 |

### 2. Grammar（语法）

检查时态、主谓一致、冠词、介词、单复数、语序和句子结构等问题。

例如：

| 原文 | 修改建议 | 中文说明 |
|---|---|---|
| She go to work every day. | She goes to work every day. | 一般现在时中，第三人称单数主语的谓语动词通常需要加 `-s`。 |

### 3. More Natural Expressions（更地道的表达）

针对语法正确但不够自然的表达，提供更符合英语习惯的替代方案。

例如：

| 原文 | 建议表达 | 中文说明 |
|---|---|---|
| I very like this idea. | I really like this idea. | 英语中通常使用 really 修饰 like，而不是直接使用 very。 |

需要特别注意：**语法错误与表达优化是两回事。** Skill 不应将所有非母语表达都判定为错误，也不应为了显示批改价值而强行修改原文。

### 4. Learning Summary（学习总结）

在报告末尾总结：

- **Key Takeaways**：本次最值得学习的语言知识点，最多三项。
- **Useful Expression**：一个实用表达，附中文释义和示例。
- **Overall Feedback**：简短、具体、客观的写作反馈。

## 文件修改规则

English Coach 采用保守的文件修改策略。

1. 原文章保持不变，不进行行内纠错或自动重写。
2. 在文章末尾追加 `## English Review`。
3. 如果已经存在由 Skill 生成的批改报告，则更新已有报告，而不是重复追加。
4. 保留其他章节、链接、代码块、引用和技术术语。
5. 修改前必须读取原文件，修改后必须验证结果。
6. 如果无法安全确定已有报告的边界，应先询问用户，不得冒险覆盖其他内容。
7. 只有在文件确实写入成功后，才能向用户报告完成。

## 设计原则

### 准确性优先

不为了增加批改数量而制造错误。原文正确且自然时，应明确指出，不必强行修改。

### 区分错误与优化

将明确的拼写、用词和语法错误，与可选的风格优化分开，避免用户混淆。

### 保留作者风格

优化应以准确、自然、清晰为目标，而不是将简单的英语改写成复杂、刻意的表达。

### 从自己的文章中学习

每次批改不仅改善当前文章，还应帮助作者理解错误原因，积累可复用的语法规则、固定搭配和地道表达。

## 已知限制

- 批改质量取决于所使用的模型及其上下文处理能力。
- 有歧义的句子可能需要作者补充说明。
- 较长的文章可能需要分段处理，最后汇总成一份完整报告。
- 对于正式出版或其他高要求场景，仍建议进行人工审校。
- 文件引用、路径解析和写入权限取决于 Claude Code 的运行环境及项目配置。

## 许可证

MIT