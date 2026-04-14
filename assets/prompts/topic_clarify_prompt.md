请根据以下输入，生成一张结构化 TopicCard。

输入信息：
- 学段：{school_stage}
- 学科：{subject}
- 教学问题：{teaching_problem}
- 研究场景：{research_context}

请只输出严格 JSON，不要输出解释文字，不要使用 Markdown 代码块。

JSON 字段要求：
{{
  "title": "研究题目，中文，明确具体",
  "topic_candidates": ["候选题目1", "候选题目2", "候选题目3"],
  "research_problem": "一句话概括核心研究问题",
  "research_questions": ["研究问题1", "研究问题2", "研究问题3"],
  "target_population": "研究对象，例如某学段学生、教师或课程场景",
  "context": "研究开展场景",
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4"],
  "recommended_methods": ["方法1", "方法2"],
  "mentor_analysis": "80-180字，说明为什么这个选题成立、适合怎样的教师科研写作路径"
}}

要求：
- 题目要符合中国教师教研/科研表达习惯。
- 候选题目给出 3-5 个，风格接近但切入点略有差异。
- 研究问题要适合进一步写摘要、背景、文献综述和方法设计。
- 推荐方法优先使用教师容易落地的方法，如案例研究、行动研究、问卷调查、访谈、课堂观察、教学实验。
