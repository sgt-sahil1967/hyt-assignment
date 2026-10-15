# Explanation rating sheet (rate 1-5 per criterion BEFORE looking at judge scores)

Score the explanation 1-5 on each criterion:
- groundedness: every claim is supported by the scorer output / resume (5 = fully supported; 1 = invents skills or facts).
- gap_correctness: the gaps it names are the real missing/weak requirements in the scorer output, none invented,
  none important omitted (5 = exact; 1 = wrong or missing the main gap).
- specificity: names concrete requirements, evidence and reasons rather than generic statements (5 = very specific).
- usefulness: a recruiter could act on it (understands why advanced/escalated and what to check) (5 = very useful).


## JD01 / R023 — Java Software Engineer - Hybrid 1 day a month in the Leeds office

Scorer output:
```json
{
 "score": 0.2833,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": 0.375,
  "experience": 1.0,
  "role_relevance": 0.3281
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "java",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Java"
  },
  {
   "requirement": "spring boot",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "Built REST APIs"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "monitoring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "restful design",
   "level": "nice",
   "strength": 1.0,
   "basis": "used",
   "quote": "Built REST APIs"
  },
  {
   "requirement": "api gateway",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: spring boot",
  "missing must-have: ci/cd",
  "missing must-have: monitoring",
  "missing nice-have: api gateway",
  "missing nice-have: ci/cd"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Leicester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Django, Java, REST APIs, C++, React, Docker
Experience
Full Stack Developer at DataWave Technologies (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2833 for the Java Software Engineer position. The strongest evidence for their candidacy is their experience with "Built REST APIs" and "Java". Key gaps include missing requirements for spring boot, ci/cd, monitoring, and api gateway. The application has been escalated for further review despite the low fit and missing must-have qualifications.


## JD01 / R028 — Java Software Engineer - Hybrid 1 day a month in the Leeds office

Scorer output:
```json
{
 "score": 0.2333,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.1667,
  "nice_to_have": 0.375,
  "experience": 1.0,
  "role_relevance": 0.3281
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "java",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "spring boot",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "monitoring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "restful design",
   "level": "nice",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "api gateway",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: java",
  "missing must-have: spring boot",
  "missing must-have: ci/cd",
  "missing must-have: monitoring",
  "missing nice-have: api gateway",
  "missing nice-have: ci/cd"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Liverpool, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
C++, Node.js, AWS, Docker, SQL, Python
Experience
Full Stack Developer at CloudBridge UK (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Birmingham (2017)
```

Explanation:
> This candidate has an overall fit score of 0.2333 for the Java Software Engineer position. The strongest evidence of their qualifications is their experience with "REST API" and "Docker". Key gaps include a lack of required experience in java, spring boot, ci/cd, and monitoring. This application has been escalated for manual review despite the missing must-have requirements and low overall fit.


## JD01 / R066 — Java Software Engineer - Hybrid 1 day a month in the Leeds office

Scorer output:
```json
{
 "score": 0.2445,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.1667,
  "nice_to_have": 0.375,
  "experience": 1.0,
  "role_relevance": 0.4525
 },
 "years_experience": 3.54,
 "evidence": [
  {
   "requirement": "java",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "spring boot",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "monitoring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "restful design",
   "level": "nice",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "api gateway",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->containerisation",
   "quote": "Kubernetes"
  },
  {
   "requirement": "ci/cd",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: java",
  "missing must-have: spring boot",
  "missing must-have: ci/cd",
  "missing must-have: monitoring",
  "missing nice-have: api gateway",
  "missing nice-have: ci/cd"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, AWS, JavaScript, Kubernetes, Git, SQL
Experience
Senior Software Engineer at NextGen Systems (2020 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall score of 0.24 for the Java Software Engineer position, indicating a low fit. The strongest evidence for the role is their experience with "REST API" and "Kubernetes". Key gaps include a lack of required experience in java, spring boot, ci/cd, and monitoring. Despite these missing must-have qualifications, the application has been escalated for further review.


## JD01 / R091 — Java Software Engineer - Hybrid 1 day a month in the Leeds office

Scorer output:
```json
{
 "score": 0.2445,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.1667,
  "nice_to_have": 0.375,
  "experience": 1.0,
  "role_relevance": 0.4525
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "java",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "spring boot",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "monitoring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "restful design",
   "level": "nice",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "api gateway",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->containerisation",
   "quote": "Kubernetes"
  },
  {
   "requirement": "ci/cd",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: java",
  "missing must-have: spring boot",
  "missing must-have: ci/cd",
  "missing must-have: monitoring",
  "missing nice-have: api gateway",
  "missing nice-have: ci/cd"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Leicester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Django, JavaScript, React, Kubernetes, Docker, Machine Learning
Experience
Senior Software Engineer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate has an overall fit score of 0.24 for the Java Software Engineer position. The strongest evidence is their experience with "REST API" and "Kubernetes". Key gaps include missing requirements for Java, Spring Boot, CI/CD, monitoring, and API gateway. This application was escalated for manual review despite the low fit and missing must-have qualifications.


## JD01 / R096 — Java Software Engineer - Hybrid 1 day a month in the Leeds office

Scorer output:
```json
{
 "score": 0.2806,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.4167,
  "nice_to_have": 0.25,
  "experience": 0.77,
  "role_relevance": 0.4525
 },
 "years_experience": 1.54,
 "evidence": [
  {
   "requirement": "java",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:spring boot->java",
   "quote": "Spring Boot"
  },
  {
   "requirement": "spring boot",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Spring Boot"
  },
  {
   "requirement": "api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "monitoring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "restful design",
   "level": "nice",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "api gateway",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: ci/cd",
  "missing must-have: monitoring",
  "missing nice-have: api gateway",
  "missing nice-have: containerisation",
  "missing nice-have: ci/cd",
  "experience 1.5y below implied 2y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Manchester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Spring Boot, Python, Node.js, Java, SQL, Git
Experience
Senior Software Engineer at NextGen Systems (2022 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.28, indicating a low match for the Java Software Engineer position. The strongest evidence for the candidate is their experience with "REST API" and "Spring Boot". Key gaps include a lack of experience in ci/cd, monitoring, api gateway, and containerisation, as well as having only 1.54 years of experience. Despite these missing must-have requirements and low overall fit, the application has been escalated for further review.


## JD03 / R008 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.2417,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": 0.1,
  "experience": 0.6486,
  "role_relevance": 0.6099
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Git"
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:aws->cloud",
   "quote": "AWS"
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: nodejs",
  "missing must-have: ruby",
  "missing must-have: sql",
  "missing must-have: ci/cd",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 4.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Nottingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
JavaScript, Docker, Git, Kubernetes, AWS, React
Experience
Software Engineer at NextGen Systems (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate for the Senior Full Stack Software Developer position received an overall fit score of 0.24. The strongest evidence for their application is their experience with "REST API", "React", "Git", "Docker", and "AWS". Key gaps include a lack of experience with nodejs, ruby, sql, and ci/cd, as well as having only 4.5 years of experience. Despite the low fit and missing must-have requirements, this application has been escalated for further review.


## JD03 / R012 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.1908,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.2778,
  "nice_to_have": 0.1,
  "experience": 0.3629,
  "role_relevance": 0.6099
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Node.js"
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "Built REST APIs"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: ruby",
  "missing must-have: sql",
  "missing must-have: git",
  "missing must-have: ci/cd",
  "missing must-have: cloud computing",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 2.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Sheffield, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Kubernetes, Node.js, React, Docker, REST APIs, Spring Boot
Experience
Software Engineer at BrightCode Solutions (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall score of 0.19 for the Senior Full Stack Software Developer position. The strongest evidence of their technical capability is that they "Built REST APIs," alongside listed experience with "Node.js," "React," and "Docker." Significant gaps include a lack of experience with ruby, sql, git, ci/cd, and cloud computing, as well as only 2.5 years of experience compared to the requirement. Despite the low fit and missing must-have requirements, this application has been escalated for further review.


## JD03 / R029 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.2347,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3889,
  "nice_to_have": 0.1,
  "experience": 0.3629,
  "role_relevance": 0.7272
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Node.js"
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "Built REST APIs"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "SQL"
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:aws->cloud",
   "quote": "AWS"
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:react->javascript",
   "quote": "React"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: ruby",
  "missing must-have: git",
  "missing must-have: ci/cd",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 2.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Birmingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Docker, AWS, React, SQL, REST APIs, Node.js
Experience
Full Stack Developer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.23 for the Senior Full Stack Software Developer position. The strongest evidence of their technical capability is that they have "Built REST APIs" and listed experience with Node.js, React, SQL, Docker, and AWS. Key gaps include a lack of experience with ruby, git, and ci/cd, as well as having only 2.5 years of experience compared to the requirement. The application has been escalated for manual review despite the low fit and missing must-have requirements.


## JD03 / R041 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.1862,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.2222,
  "nice_to_have": 0.1,
  "experience": 0.3629,
  "role_relevance": 0.7442
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "Built REST APIs"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Git"
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: nodejs",
  "missing must-have: ruby",
  "missing must-have: sql",
  "missing must-have: docker",
  "missing must-have: ci/cd",
  "missing must-have: cloud computing",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 2.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Birmingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Git, JavaScript, Spring Boot, REST APIs, React
Experience
Senior Software Engineer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Birmingham (2017)
```

Explanation:
> This candidate received an overall fit score of 0.1862 for the Senior Full Stack Software Developer position. The strongest evidence of their qualifications is their experience where they "Built REST APIs," alongside listed experience with React and Git. Significant gaps exist, including missing must-have requirements for nodejs, ruby, sql, docker, ci/cd, and cloud computing, as well as a total of 2.54 years of experience. Despite the low fit and missing must-have skills, this application has been escalated for further review.


## JD03 / R048 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.1847,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.2222,
  "nice_to_have": 0.1,
  "experience": 0.3629,
  "role_relevance": 0.7272
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Node.js"
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Git"
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: ruby",
  "missing must-have: reactjs",
  "missing must-have: sql",
  "missing must-have: docker",
  "missing must-have: ci/cd",
  "missing must-have: cloud computing",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 2.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Sheffield, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Git, Machine Learning, Node.js, Java, C++
Experience
Full Stack Developer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.18 for the Senior Full Stack Software Developer position. The strongest evidence of their qualifications includes experience with "REST API", "Node.js", and "Git". Key gaps include a lack of required experience in ruby, reactjs, sql, docker, ci/cd, and cloud computing, as well as having only 2.5 years of experience. Despite these missing requirements and low overall fit, the application has been escalated for further review.


## JD03 / R091 — Senior Full Stack Software Developer (Nodejs)- Birmingham, UK

Scorer output:
```json
{
 "score": 0.1862,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.2222,
  "nice_to_have": 0.1,
  "experience": 0.3629,
  "role_relevance": 0.7442
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "nodejs",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ruby",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "reactjs",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "rest api",
   "level": "must",
   "strength": 1.0,
   "basis": "used",
   "quote": "REST API"
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "docker",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Docker"
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "cloud computing",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html5",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "graphql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: nodejs",
  "missing must-have: ruby",
  "missing must-have: sql",
  "missing must-have: git",
  "missing must-have: ci/cd",
  "missing must-have: cloud computing",
  "missing nice-have: html5",
  "missing nice-have: css",
  "missing nice-have: graphql",
  "missing nice-have: typescript",
  "experience 2.5y below 7y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Leicester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Django, JavaScript, React, Kubernetes, Docker, Machine Learning
Experience
Senior Software Engineer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate has an overall fit score of 0.1862 for the Senior Full Stack Software Developer position. The strongest evidence of their qualifications includes experience with "REST API", "React", "Docker", and "JavaScript". Key gaps include a lack of several required technical skills such as nodejs, ruby, sql, git, ci/cd, and cloud computing, as well as having only 2.54 years of experience. Despite the low fit and missing must-have requirements, this application has been escalated for further review.


## JD04 / R011 — Software Engineer / SRE (AWS, Spring, Microservices)

Scorer output:
```json
{
 "score": 0.215,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.1667,
  "nice_to_have": 0.0,
  "experience": 1.0,
  "role_relevance": 0.5001
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "spring",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:spring boot->spring",
   "quote": "Spring Boot"
  },
  {
   "requirement": "scripting",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "infrastructure as code",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: scripting",
  "missing must-have: containerisation",
  "missing must-have: infrastructure as code",
  "missing must-have: ci/cd",
  "missing nice-have: devops"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Leicester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Machine Learning, Node.js, Spring Boot, C++, JavaScript, AWS
Experience
Senior Software Engineer at BrightCode Solutions (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall fit score of 0.215 for the Software Engineer / SRE position. The strongest evidence for their candidacy includes experience with "AWS" and "Spring Boot". Key gaps include a lack of required experience in scripting, containerisation, infrastructure as code, and ci/cd. Despite the low fit, missing must-have requirements, and a location mismatch, the application has been escalated for further review.


## JD04 / R028 — Software Engineer / SRE (AWS, Spring, Microservices)

Scorer output:
```json
{
 "score": 0.2759,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": 0.5,
  "experience": 1.0,
  "role_relevance": 0.399
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "spring",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "scripting",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:python->scripting",
   "quote": "Python"
  },
  {
   "requirement": "containerisation",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "infrastructure as code",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->devops",
   "quote": "Docker"
  }
 ],
 "gaps": [
  "missing must-have: spring",
  "missing must-have: infrastructure as code",
  "missing must-have: ci/cd"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Liverpool, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
C++, Node.js, AWS, Docker, SQL, Python
Experience
Full Stack Developer at CloudBridge UK (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Birmingham (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2759 for the Software Engineer / SRE position. Their strongest evidence includes experience with "AWS", "Python", and "Docker". Key gaps identified in their profile include a lack of experience with spring, infrastructure as code, and ci/cd. Despite the low fit score, missing must-have requirements, and a location mismatch, this application has been escalated for further review.


## JD04 / R052 — Software Engineer / SRE (AWS, Spring, Microservices)

Scorer output:
```json
{
 "score": 0.2369,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": 0.0,
  "experience": 1.0,
  "role_relevance": 0.4659
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "spring",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:spring boot->spring",
   "quote": "Spring Boot"
  },
  {
   "requirement": "scripting",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:django->scripting",
   "quote": "Django"
  },
  {
   "requirement": "containerisation",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "infrastructure as code",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: containerisation",
  "missing must-have: infrastructure as code",
  "missing must-have: ci/cd",
  "missing nice-have: devops"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Leeds, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Spring Boot, Django, Java, REST APIs, React, AWS
Experience
Junior Software Engineer at DataWave Technologies (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall score of 0.24 for the Software Engineer / SRE position. Their strongest evidence includes experience with "AWS", "Spring Boot", and "Django". Key gaps include a lack of experience in containerisation, infrastructure as code, and ci/cd. The application was escalated for manual review despite a low fit, missing must-have requirements, and a location mismatch.


## JD04 / R097 — Software Engineer / SRE (AWS, Spring, Microservices)

Scorer output:
```json
{
 "score": 0.2081,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.1667,
  "nice_to_have": 0.0,
  "experience": 1.0,
  "role_relevance": 0.4237
 },
 "years_experience": 3.54,
 "evidence": [
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "spring",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:spring boot->spring",
   "quote": "Spring Boot"
  },
  {
   "requirement": "scripting",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "infrastructure as code",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "ci/cd",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: scripting",
  "missing must-have: containerisation",
  "missing must-have: infrastructure as code",
  "missing must-have: ci/cd",
  "missing nice-have: devops"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Cambridge, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Node.js, AWS, Spring Boot, React, C++, Git
Experience
Backend Developer at TechNova Ltd (2020 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.21 for the Software Engineer / SRE role. The strongest evidence of their qualifications includes experience with "AWS" and "Spring Boot". Key gaps include a lack of experience in scripting, containerisation, infrastructure as code, and ci/cd. Despite the low fit, missing must-have requirements, and a location mismatch, this application has been escalated for further review.


## JD05 / R008 — AI Software Developer

Scorer output:
```json
{
 "score": 0.2433,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": 0.25,
  "experience": 1.0,
  "role_relevance": 0.2865
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: machine learning",
  "missing must-have: c#",
  "missing must-have: sql",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: nosql"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Nottingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
JavaScript, Docker, Git, Kubernetes, AWS, React
Experience
Software Engineer at NextGen Systems (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall score of 0.2433 for the AI Software Developer position. The strongest evidence for their application is a computer science degree and 4.54 years of experience, alongside familiarity with "JavaScript", "React", and "Docker". Key gaps include the absence of required machine learning, C#, and SQL expertise, as well as missing nice-to-have skills like .NET, TypeScript, and NoSQL. The application has been escalated for further review despite the low fit and missing must-have requirements.


## JD05 / R009 — AI Software Developer

Scorer output:
```json
{
 "score": 0.262,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.0833,
  "experience": 1.0,
  "role_relevance": 0.2444
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "SQL"
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: machine learning",
  "missing must-have: c#",
  "missing nice-have: .net",
  "missing nice-have: javascript",
  "missing nice-have: typescript",
  "missing nice-have: react.js",
  "missing nice-have: nosql"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Sheffield, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Docker, SQL, C++, REST APIs, Python, Kubernetes
Experience
Full Stack Developer at DataWave Technologies (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.262 for the AI Software Developer position. Their strongest evidence includes a computer science degree and experience with "SQL" and "Docker" for containerisation. Key gaps include the absence of machine learning, C#, .NET, JavaScript, TypeScript, React.js, and NoSQL. Despite the low fit and missing must-have requirements, the application has been escalated for further review due to the candidate's 5.54 years of relevant experience.


## JD05 / R026 — AI Software Developer

Scorer output:
```json
{
 "score": 0.1886,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.25,
  "experience": 0.27,
  "role_relevance": 0.2358
 },
 "years_experience": 0.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Machine Learning"
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:react->javascript",
   "quote": "React"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->containerisation",
   "quote": "Kubernetes"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: c#",
  "missing must-have: sql",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: nosql",
  "experience 0.5y below 2y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Git, Kubernetes, Docker, Machine Learning, C++, React
Experience
Senior Software Engineer at BrightCode Solutions (2023 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.1886 for the AI Software Developer position. The strongest evidence for their application is their background in "Machine Learning," "React," and "Kubernetes." Key gaps include a lack of experience with C#, SQL, .NET, TypeScript, and NoSQL, as well as having less than two years of experience. This profile has been escalated for review despite the missing must-have requirements and low overall fit.


## JD05 / R028 — AI Software Developer

Scorer output:
```json
{
 "score": 0.2695,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.1667,
  "experience": 1.0,
  "role_relevance": 0.2444
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "SQL"
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: machine learning",
  "missing must-have: c#",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: react.js",
  "missing nice-have: nosql"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Liverpool, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
C++, Node.js, AWS, Docker, SQL, Python
Experience
Full Stack Developer at CloudBridge UK (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Birmingham (2017)
```

Explanation:
> This candidate received an overall fit score of 0.27 for the AI Software Developer position. Their strongest evidence includes a computer science degree, as well as experience with "SQL", "Node.js", and "Docker". Key gaps include missing requirements for machine learning, C#, .NET, typescript, react.js, and nosql. The application has been escalated for further review despite the low fit and missing must-have qualifications.


## JD05 / R033 — AI Software Developer

Scorer output:
```json
{
 "score": 0.2686,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.1667,
  "experience": 1.0,
  "role_relevance": 0.2343
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Machine Learning"
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->containerisation",
   "quote": "Docker"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: c#",
  "missing must-have: sql",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: react.js",
  "missing nice-have: nosql"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Spring Boot, Docker, Machine Learning, Kubernetes, JavaScript, Node.js
Experience
Junior Software Engineer at CloudBridge UK (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.27 for the AI Software Developer position. Their strongest evidence is a computer science degree and experience with "Machine Learning", "JavaScript", and "Docker". Key gaps include the absence of C#, SQL, .NET, TypeScript, React.js, and NoSQL. The application has been escalated for further review despite missing mandatory requirements and a low overall fit.


## JD05 / R048 — AI Software Developer

Scorer output:
```json
{
 "score": 0.262,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.0833,
  "experience": 1.0,
  "role_relevance": 0.2444
 },
 "years_experience": 2.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Machine Learning"
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: c#",
  "missing must-have: sql",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: react.js",
  "missing nice-have: containerisation",
  "missing nice-have: nosql"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Sheffield, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Git, Machine Learning, Node.js, Java, C++
Experience
Full Stack Developer at DataWave Technologies (2021 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.262 for the AI Software Developer position. The strongest evidence for their application is a computer science degree and experience listed as "Machine Learning". Key gaps include missing requirements for C#, SQL, .NET, TypeScript, React.js, containerisation, and NoSQL. The application has been escalated for manual review despite the missing must-have skills and low overall fit.


## JD05 / R078 — AI Software Developer

Scorer output:
```json
{
 "score": 0.2411,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.375,
  "nice_to_have": 0.1667,
  "experience": 0.77,
  "role_relevance": 0.2358
 },
 "years_experience": 1.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "machine learning",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Machine Learning"
  },
  {
   "requirement": "c#",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": ".net",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:react->javascript",
   "quote": "React"
  },
  {
   "requirement": "typescript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react.js",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "containerisation",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: c#",
  "missing must-have: sql",
  "missing nice-have: .net",
  "missing nice-have: typescript",
  "missing nice-have: containerisation",
  "missing nice-have: nosql",
  "experience 1.5y below 2y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Nottingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Machine Learning, React, Django, Node.js, AWS, Java
Experience
Senior Software Engineer at DataWave Technologies (2022 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2411 for the AI Software Developer position. Their strongest evidence is a computer science degree and experience listed as "Machine Learning". Key gaps include missing requirements for C#, SQL, .NET, TypeScript, containerisation, and NoSQL, alongside having less than two years of experience. The application has been escalated for manual review despite the missing must-have skills and low overall fit.


## JD06 / R019 — Junior Software Engineer

Scorer output:
```json
{
 "score": 0.3017,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "CAREER_SWITCH",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.5,
  "nice_to_have": 0.1875,
  "experience": 1.0,
  "role_relevance": 0.1652
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "web development frameworks",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Django"
  },
  {
   "requirement": "sql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->devops",
   "quote": "Docker"
  },
  {
   "requirement": "pytest",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: git",
  "missing nice-have: sql",
  "missing nice-have: nosql",
  "missing nice-have: html",
  "missing nice-have: css",
  "missing nice-have: pytest"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Bristol, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Node.js, AWS, Docker, JavaScript, Python, Django
Experience
Full Stack Developer at TechNova Ltd (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.30, indicating they fall below the standard threshold for the Junior Software Engineer role. Their strongest evidence includes a computer science degree and experience listed as "Python", "Django", "Node.js", and "Docker". Key gaps include missing requirements for git, sql, nosql, html, css, and pytest. The application has been escalated for review due to the missing must-have requirement, the candidate's career switch, and the low overall score.


## JD06 / R047 — Junior Software Engineer

Scorer output:
```json
{
 "score": 0.3153,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.5,
  "nice_to_have": 0.125,
  "experience": 1.0,
  "role_relevance": 0.3785
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:django->python",
   "quote": "Django"
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "web development frameworks",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Django"
  },
  {
   "requirement": "sql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->devops",
   "quote": "Kubernetes"
  },
  {
   "requirement": "pytest",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: git",
  "missing nice-have: sql",
  "missing nice-have: nosql",
  "missing nice-have: html",
  "missing nice-have: css",
  "missing nice-have: javascript",
  "missing nice-have: pytest"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Sheffield, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Django, Kubernetes, REST APIs, Machine Learning, Docker, Java
Experience
Senior Software Engineer at BrightCode Solutions (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Nottingham (2017)
```

Explanation:
> This candidate is a low fit for the Junior Software Engineer role with an overall score of 0.3153. The strongest evidence for their candidacy is their relevant experience and background, supported by their work with "Django" and "Kubernetes". Key gaps include a missing must-have requirement for git, as well as several missing nice-to-have skills such as sql, nosql, html, css, javascript, and pytest. Despite the low score and missing requirements, the application has been escalated for further review.


## JD06 / R054 — Junior Software Engineer

Scorer output:
```json
{
 "score": 0.2773,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": 0.125,
  "experience": 1.0,
  "role_relevance": 0.5119
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "web development frameworks",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:node.js->javascript",
   "quote": "Node.js"
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->devops",
   "quote": "Kubernetes"
  },
  {
   "requirement": "pytest",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: python",
  "missing must-have: git",
  "missing nice-have: web development frameworks",
  "missing nice-have: sql",
  "missing nice-have: nosql",
  "missing nice-have: html",
  "missing nice-have: css",
  "missing nice-have: pytest"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Node.js, Kubernetes, Machine Learning, JavaScript, REST APIs, Java
Experience
Junior Software Engineer at DataWave Technologies (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2773 for the Junior Software Engineer position. Their strongest evidence includes experience with "Node.js" and "Kubernetes," which relate to the javascript and devops requirements. Key gaps include missing must-have qualifications in python and git, as well as several nice-to-have skills like web development frameworks, sql, nosql, html, css, and pytest. Despite these missing requirements and a low overall fit, the application has been escalated for further review.


## JD06 / R066 — Junior Software Engineer

Scorer output:
```json
{
 "score": 0.6182,
 "decision": "advance",
 "reason_codes": [],
 "components": {
  "must_have": 0.6667,
  "nice_to_have": 0.1875,
  "experience": 1.0,
  "role_relevance": 0.3785
 },
 "years_experience": 3.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Git"
  },
  {
   "requirement": "web development frameworks",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "sql",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "SQL"
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "JavaScript"
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:kubernetes->devops",
   "quote": "Kubernetes"
  },
  {
   "requirement": "pytest",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing nice-have: web development frameworks",
  "missing nice-have: nosql",
  "missing nice-have: html",
  "missing nice-have: css",
  "missing nice-have: pytest"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, AWS, JavaScript, Kubernetes, Git, SQL
Experience
Senior Software Engineer at NextGen Systems (2020 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate is a solid fit for the Junior Software Engineer role with an overall score of 0.62. The strongest evidence is their computer science degree and 3.54 years of relevant experience. Key gaps include a lack of experience with web development frameworks, nosql, html, css, and pytest. The candidate was advanced because they meet the core requirements, including "Python", "Git", "SQL", "JavaScript", and "Kubernetes".


## JD06 / R100 — Junior Software Engineer

Scorer output:
```json
{
 "score": 0.3017,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "CAREER_SWITCH",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.5,
  "nice_to_have": 0.1875,
  "experience": 1.0,
  "role_relevance": 0.1652
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "git",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "web development frameworks",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Django"
  },
  {
   "requirement": "sql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "nosql",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "html",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "css",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "javascript",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:react->javascript",
   "quote": "React"
  },
  {
   "requirement": "devops",
   "level": "nice",
   "strength": 0.5,
   "basis": "listed+taxonomy:docker->devops",
   "quote": "Docker"
  },
  {
   "requirement": "pytest",
   "level": "nice",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: git",
  "missing nice-have: sql",
  "missing nice-have: nosql",
  "missing nice-have: html",
  "missing nice-have: css",
  "missing nice-have: pytest"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Manchester, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Docker, Django, React, Node.js, Spring Boot
Experience
Full Stack Developer at TechNova Ltd (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall fit score of 0.30, which is below the standard threshold for the Junior Software Engineer role. The strongest evidence for their application includes a computer science degree and experience with "Python", "Django", "React", and "Docker". Key gaps include missing requirements for git, sql, nosql, html, css, and pytest. This profile has been escalated for review due to the missing must-have skill, the candidate's background as a career switcher, and the low overall score.


## JD09 / R008 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.3131,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.513
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: python",
  "missing must-have: vue.js",
  "missing must-have: node.js"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Nottingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
JavaScript, Docker, Git, Kubernetes, AWS, React
Experience
Software Engineer at NextGen Systems (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.3131 for the Senior Software Engineer position. Their strongest evidence includes a computer science degree, as well as experience listed with "React" and "AWS". Key gaps include missing must-have requirements for python, vue.js, and node.js. Despite missing several required skills and falling below the standard scoring threshold, this application has been escalated for further review.


## JD09 / R019 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.3361,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.4167,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.4524
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Node.js"
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: vue.js",
  "missing must-have: react"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Bristol, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Node.js, AWS, Docker, JavaScript, Python, Django
Experience
Full Stack Developer at TechNova Ltd (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.3361 for the Senior Software Engineer position. Their strongest evidence includes a computer science degree and listed experience with "Python", "Node.js", and "AWS". Key gaps include missing must-have requirements for vue.js and react. The application was escalated for manual review despite falling below the automated threshold and missing specific required skills.


## JD09 / R026 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.1756,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": null,
  "experience": 0.135,
  "role_relevance": 0.6456
 },
 "years_experience": 0.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: python",
  "missing must-have: vue.js",
  "missing must-have: node.js",
  "missing must-have: aws",
  "experience 0.5y below implied 4y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Git, Kubernetes, Docker, Machine Learning, C++, React
Experience
Senior Software Engineer at BrightCode Solutions (2023 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.1756 for the Senior Software Engineer position. The strongest evidence for their application is their background in "React" and the possession of a computer science degree. Key gaps include a lack of experience with python, vue.js, node.js, and aws, as well as having 0.5 years of experience compared to the implied 4-year requirement. This profile was escalated for manual review despite the low fit and missing must-have requirements.


## JD09 / R035 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.2969,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": null,
  "experience": 0.885,
  "role_relevance": 0.513
 },
 "years_experience": 3.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: vue.js",
  "missing must-have: node.js",
  "missing must-have: react",
  "experience 3.5y below implied 4y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Cambridge, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
AWS, Java, Python, Docker, Git, Machine Learning
Experience
Software Engineer at DataWave Technologies (2020 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2969 for the Senior Software Engineer position. Their strongest evidence includes a computer science degree and experience listed with "Python" and "AWS". Key gaps include missing requirements for vue.js, node.js, and react, as well as having 3.54 years of experience which is below the implied requirement. The application was escalated for manual review despite the low fit and missing must-have skills.


## JD09 / R043 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.2837,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.513
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: python",
  "missing must-have: vue.js",
  "missing must-have: node.js",
  "missing must-have: aws"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Birmingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Git, Java, JavaScript, Kubernetes, REST APIs, React
Experience
Software Engineer at NextGen Systems (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall fit score of 0.28, indicating a low match for the Senior Software Engineer position. The strongest evidence for their candidacy is their possession of a computer science degree and some experience with "React". Key gaps include a lack of required experience in python, vue.js, node.js, and aws. Despite these missing must-have qualifications, the application has been escalated for further review due to the candidate's overall professional experience.


## JD09 / R050 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.2051,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": null,
  "experience": 0.135,
  "role_relevance": 0.6456
 },
 "years_experience": 0.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "React"
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: vue.js",
  "missing must-have: node.js",
  "missing must-have: aws",
  "experience 0.5y below implied 4y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Birmingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Django, Machine Learning, SQL, React, Kubernetes
Experience
Senior Software Engineer at CloudBridge UK (2023 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate received an overall fit score of 0.2051 for the Senior Software Engineer position. Their strongest evidence includes a computer science degree and experience listed as "Python" and "React". Key gaps include missing requirements for vue.js, node.js, and aws, as well as having 0.5 years less experience than the implied four-year requirement. Despite the low fit and missing must-have skills, the application has been escalated for further review.


## JD09 / R066 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.3109,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.3333,
  "nice_to_have": null,
  "experience": 0.885,
  "role_relevance": 0.6456
 },
 "years_experience": 3.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Python"
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "AWS"
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: vue.js",
  "missing must-have: node.js",
  "missing must-have: react",
  "experience 3.5y below implied 4y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, AWS, JavaScript, Kubernetes, Git, SQL
Experience
Senior Software Engineer at NextGen Systems (2020 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall score of 0.31 for the Senior Software Engineer position. Their strongest evidence includes a computer science degree and experience listed with "Python" and "AWS". However, the application has significant gaps, specifically missing the required vue.js, node.js, and react skills, while also falling slightly below the expected years of experience. Despite these missing requirements and a low score, the application has been escalated for further review.


## JD09 / R075 — Senior Software Engineer

Scorer output:
```json
{
 "score": 0.1512,
 "decision": "escalate",
 "reason_codes": [
  "MISSING_MUST_HAVE",
  "LOW_FIT"
 ],
 "components": {
  "must_have": 0.25,
  "nice_to_have": null,
  "experience": 0.135,
  "role_relevance": 0.415
 },
 "years_experience": 0.54,
 "evidence": [
  {
   "requirement": "python",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "vue.js",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "node.js",
   "level": "must",
   "strength": 0.5,
   "basis": "listed",
   "quote": "Node.js"
  },
  {
   "requirement": "react",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "aws",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  },
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: python",
  "missing must-have: vue.js",
  "missing must-have: react",
  "missing must-have: aws",
  "experience 0.5y below implied 4y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Nottingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Git, Java, C++, Machine Learning, Node.js, REST APIs
Experience
Backend Developer at NextGen Systems (2023 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.1512 for the Senior Software Engineer position. Their strongest evidence is a computer science degree and experience with "Node.js". Key gaps include a lack of experience with python, vue.js, react, and aws, as well as having 0.5 years less experience than the implied requirement. This application was escalated for manual review despite the low fit and missing must-have requirements.


## JD10 / R002 — Software Engineer

Scorer output:
```json
{
 "score": 0.4851,
 "decision": "escalate",
 "reason_codes": [
  "CAREER_SWITCH",
  "BORDERLINE_SCORE"
 ],
 "components": {
  "must_have": 0.6667,
  "nice_to_have": null,
  "experience": 0.27,
  "role_relevance": 0.1666
 },
 "years_experience": 0.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "programming languages",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:react->programming language",
   "quote": "React"
  },
  {
   "requirement": "relational database",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:sql->relational database",
   "quote": "SQL"
  }
 ],
 "gaps": [
  "experience 0.5y below implied 2y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Bristol, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
REST APIs, React, SQL, Node.js, Python, Docker
Experience
Full Stack Developer at CloudBridge UK (2023 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Manchester (2017)
```

Explanation:
> This candidate received an overall fit score of 0.4851 for the Software Engineer position. They meet the computer science degree requirement and demonstrate relevant knowledge in programming languages and relational database through "React" and "SQL". The primary gaps include a total duration of experience that is 0.5 years below the implied 2-year requirement. This application was escalated for manual review due to the candidate's career switch and a borderline automated score.


## JD10 / R004 — Software Engineer

Scorer output:
```json
{
 "score": 0.3595,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "MISSING_MUST_HAVE",
  "BELOW_THRESHOLD"
 ],
 "components": {
  "must_have": 0.5,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.3953
 },
 "years_experience": 4.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "programming languages",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:javascript->programming language",
   "quote": "JavaScript"
  },
  {
   "requirement": "relational database",
   "level": "must",
   "strength": 0.0,
   "basis": "missing",
   "quote": null
  }
 ],
 "gaps": [
  "missing must-have: relational database"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], London, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
JavaScript, React, REST APIs, Python, Django, Spring Boot
Experience
Software Engineer at DataWave Technologies (2019 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate received an overall fit score of 0.36 for the Software Engineer position. They demonstrate strong experience with 4.54 years in the field and explicitly list "JavaScript" as a programming language. However, the application is missing a required computer science degree and has no evidence of experience with a relational database. Despite being below the scoring threshold and having a location mismatch, this profile was escalated for further review due to the missing must-have requirement.


## JD10 / R017 — Software Engineer

Scorer output:
```json
{
 "score": 0.6902,
 "decision": "advance",
 "reason_codes": [
  "LOCATION_MISMATCH"
 ],
 "components": {
  "must_have": 0.6667,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.3554
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "programming languages",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:python->programming language",
   "quote": "Python"
  },
  {
   "requirement": "relational database",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:sql->relational database",
   "quote": "SQL"
  }
 ],
 "gaps": []
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Cambridge, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Python, Node.js, SQL, Kubernetes, React, Docker
Experience
Junior Software Engineer at BrightCode Solutions (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Bristol (2017)
```

Explanation:
> This candidate is a strong match for the Software Engineer role with an overall score of 0.69. They demonstrate excellent experience with 5.54 years in the field and possess the required computer science degree. While they meet the requirements for "Python" and "SQL", their overall role relevance score is lower, indicating a need to verify the depth of their technical background. The candidate has been advanced for further review despite a mismatch regarding their current location.


## JD10 / R028 — Software Engineer

Scorer output:
```json
{
 "score": 0.6568,
 "decision": "escalate",
 "reason_codes": [
  "LOCATION_MISMATCH",
  "CAREER_SWITCH"
 ],
 "components": {
  "must_have": 0.6667,
  "nice_to_have": null,
  "experience": 1.0,
  "role_relevance": 0.1666
 },
 "years_experience": 5.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "programming languages",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:c++->programming language",
   "quote": "C++"
  },
  {
   "requirement": "relational database",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:sql->relational database",
   "quote": "SQL"
  }
 ],
 "gaps": []
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Liverpool, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
C++, Node.js, AWS, Docker, SQL, Python
Experience
Full Stack Developer at CloudBridge UK (2018 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Birmingham (2017)
```

Explanation:
> This candidate is a moderate fit for the Software Engineer role with an overall score of 0.6568. They demonstrate strong professional experience and meet the computer science degree requirement, with specific proficiency in "C++" and "SQL". While there are no technical gaps identified, the application was escalated for manual review due to a mismatch with the preferred work location and a history of changing career paths.


## JD10 / R039 — Software Engineer

Scorer output:
```json
{
 "score": 0.6366,
 "decision": "advance",
 "reason_codes": [
  "LOCATION_MISMATCH"
 ],
 "components": {
  "must_have": 0.6667,
  "nice_to_have": null,
  "experience": 0.77,
  "role_relevance": 0.3586
 },
 "years_experience": 1.54,
 "evidence": [
  {
   "requirement": "computer science degree",
   "level": "must",
   "strength": 1.0,
   "basis": "degree",
   "quote": null
  },
  {
   "requirement": "programming languages",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:spring boot->programming language",
   "quote": "Spring Boot"
  },
  {
   "requirement": "relational database",
   "level": "must",
   "strength": 0.5,
   "basis": "listed+taxonomy:sql->relational database",
   "quote": "SQL"
  }
 ],
 "gaps": [
  "experience 1.5y below implied 2y"
 ]
}
```

Resume:
```
[NAME]
Address: [ADDRESS], Birmingham, UK
Email: [EMAIL]
Phone: [PHONE]
Professional Summary
Software engineer with experience building scalable applications, APIs, and cloud solutions. Strong problem‐solving skills and passion for clean code.
Skills
Spring Boot, Java, React, REST APIs, SQL, JavaScript
Experience
Senior Software Engineer at CloudBridge UK (2022 - Present)
- Developed scalable web applications
- Built REST APIs
- Collaborated with cross‐functional teams
Education
BSc Computer Science – University of Leeds (2017)
```

Explanation:
> This candidate is a moderate fit for the Software Engineer role with an overall score of 0.64. They demonstrate strong foundational qualifications, including a computer science degree and experience with "Spring Boot" and "SQL". The primary gaps include having 1.5 years of experience, which is slightly below the implied 2-year requirement. Despite a location mismatch, the candidate has been advanced for further review based on their core technical background.
