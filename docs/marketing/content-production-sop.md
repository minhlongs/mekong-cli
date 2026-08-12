# Content Production SOP

**Purpose:** Standardize content creation process for quality and efficiency

**Audience:** Content team, contractors, contributors

**Version:** 1.0  
**Last Updated:** June 20, 2026

---

## Table of Contents
1. [Content Workflow](#content-workflow)
2. [Content Templates](#content-templates)
3. [Quality Checklist](#quality-checklist)
4. [Approval Process](#approval-process)
5. [Publishing Guidelines](#publishing-guidelines)

---

## Content Workflow

### Stage 1: Ideation (1-2 days)

**Process:**
1. Content lead reviews content calendar and performance data
2. Brainstorm session (weekly) for upcoming content
3. Select topic from content bank or new idea
4. Validate SEO potential (keyword research in Ahrefs)
5. Assign writer and due date in Notion

**Deliverable:** Content brief in Notion template

---

### Stage 2: Outline (1 day)

**Writer responsibilities:**
1. Research topic (competitor content, existing Mekong docs)
2. Create detailed outline with:
   - Target keyword and SEO metadata
   - Main sections with bullet points
   - Intended CTAs (newsletter signup, demo, etc.)
   - Visual needs (screenshots, diagrams, etc.)
3. Submit outline for review

**Reviewer (Content Lead) criteria:**
- Is the angle unique or adding value?
- Is the structure logical?
- Are CTAs appropriate for funnel stage?
- Is length appropriate for topic?

**Turnaround:** 24 hours

---

### Stage 3: Draft (2-3 days)

**Writer responsibilities:**
1. Write first draft following style guide
2. Include:
   - Compelling headline (test 3 variations)
   - Hook in first paragraph (problem statement)
   - Clear structure with H2/H3 headers
   - Concrete examples and screenshots
   - Internal links to related content
   - External links to authoritative sources
   - Strong CTA (newsletter signup, trial, etc.)
3. Add meta description (155 chars max)
4. Submit draft

**Reviewer criteria:**
- Grammar and readability (Grammarly)
- Factual accuracy
- SEO optimization (keyword placement)
- Brand voice consistency
- Completeness (does it deliver on promise?)

**Turnaround:** 48-72 hours

---

### Stage 4: Visuals (1-2 days)

**Designer responsibilities:**
1. Create featured image (1200x630px for social sharing)
2. Create inline diagrams/screenshots as needed
3. Annotate screenshots with arrows and callouts
4. Optimize images (compression, alt text)
5. Create social media snippets from content

**Deliverables:**
- Featured image (PNG, <200KB)
- Inline images (optimized for web)
- Social graphics (Twitter card, LinkedIn, Instagram)

---

### Stage 5: Final Edit & SEO (1 day)

**Editor responsibilities:**
1. Proofread for typos and grammar
2. Verify all links work
3. Check alt text on images
4. Optimize for target keyword:
   - Keyword in title, H1, first paragraph
   - Keyword density 0.5-1.5%
   - LS keywords naturally included
5. Add schema markup (if applicable)
6. Update URL slug (keep short, include keyword)
7. Schedule for publishing

**Turnaround:** 24 hours

---

### Stage 6: Publishing (Same day)

**Publisher responsibilities:**
1. Create new post in WordPress/Next.js
2. Paste content, add formatting
3. Add featured image
4. Set categories and tags
5. Add YoastSEO meta data
6. Schedule publish date/time
7. Add to content calendar
8. Notify team

**Checklist before hitting publish:**
- [ ] Preview looks correct (desktop + mobile)
- [ ] All images load
- [ ] Internal links work
- [ ] CTA links correct
- [ ] Newsletter checkbox box (if lead magnet)
- [ ] Social share buttons configured

---

### Stage 7: Promotion (Ongoing)

**After publish:**
1. **Immediate (same day):**
   - Share on Twitter/X (thread or link)
   - Share on LinkedIn
   - Add to newsletter (if Thursday/Friday)
   - Post in Discord/Slack community

2. **Next 3 days:**
   - Respond to all comments
   - Engage with shares
   - Retweet relevant mentions

3. **Week 1:**
   - Create 2-3 Twitter snippets from content
   - Schedule LinkedIn repost (1 week later)
   - Consider Twitter Spaces topic based on content

4. **Ongoing:**
   - Update older content with links to new post
   - Repurpose into other formats (video, podcast, etc.)

---

## Content Templates

### Blog Post Template

```markdown
---
title: ""
date: YYYY-MM-DD
description: "" (155 chars max)
image: "/images/blog/featured/slug.jpg"
imageAlt: ""
category: ""
tags: []
author: ""
draft: false
---

## [H1: Compelling headline that includes target keyword]

[Hook: 2-3 sentences capturing attention and stating the problem]

[Transition to solution/What reader will learn]

### [H2: First main point]

[Content with examples, data, screenshots as needed]

- Bullet points
- Where helpful

### [H2: Second main point]

[Continue pattern...]

### [H2: Key takeaways]

[Summary of main points]

## Next steps

[Clear CTA: What should reader do next?]
- [ ] Newsletter signup
- [ ] Free trial
- [ ] Demo request
- [ ] Related article

---

**Related:**
- [Link to related post]
- [Link to documentation]

**Want more?** Subscribe to our newsletter [link]
```

---

### Newsletter Template

```markdown
Subject: [Emoji] [ compelling subject | < 50 chars ]

---

Hi [Name],

[Opening: Personal note or engaging question]

## This Week's Highlights

### 1. [Article title] [Link]
[1-2 sentence summary]

### 2. [Article title] [Link]
[1-2 sentence summary]

### 3. [Community highlight] [Link]
[User story or win]

## From Our Community
[User quote or achievement]

## What We're Building
[Product update or upcoming feature]

## Coming Up Next Week
[Teaser for upcoming content]

---

[CTA Button: Subscribe → Upgrade → Try Free]

---
To unsubscribe, [click here].
Sent to ___ subscribers.
```

---

## Quality Checklist

### Before Publishing

**Content Quality:**
- [ ] Title is compelling and includes target keyword
- [ ] Hook captures attention in first 2 paragraphs
- [ ] Structure is logical with clear H2/H3 headers
- [ ] Content delivers on headline promise
- [ ] Examples are concrete and relevant
- [ ] Screenshots are clear and annotated
- [ ] Internal links point to relevant content
- [ ] External links are authoritative and open in new tab
- [ ] CTA is clear and appropriate for funnel stage
- [ ] Length is appropriate (1,500-4,000 words)

**SEO:**
- [ ] Target keyword in title, H1, first paragraph, meta description
- [ ] Keyword density 0.5-1.5%
- [ ] LSI keywords naturally included
- [ ] Meta description < 155 characters
- [ ] URL slug is short and includes keyword
- [ ] Alt text on all images includes keyword where relevant
- [ ] Internal linking to 3-5 related posts
- [ ] Schema markup added (HowTo, Article, etc.)

**Technical:**
- [ ] All links work (internal and external)
- [ ] Images optimized (<200KB, correct dimensions)
- [ ] Mobile preview looks good
- [ ] No broken HTML or markdown
- [ ] Featured image is 1200x630px
- [ ] Social share images correct

**Brand:**
- [ ] Voice is confident, educational, not salesy
- [ ] No jargon without explanation
- [ ] Consistent with brand guidelines
- [ ] Links to mekongmind.com correctly
- [ ] No competitor disparagement

---

## Approval Process

### Tier 1: Standard Content
- **Process:** Writer → Content Lead → Publish
- **Timeline:** 5-7 days total
- **Content types:** Blog posts, social media, newsletters

### Tier 2: Key Content
- **Process:** Writer → Content Lead → Founder → Publish
- **Timeline:** 7-10 days total
- **Content types:** Major announcements, thought leadership, video scripts

### Tier 3: Public-Facing Documentation
- **Process:** Writer → Content Lead → Tech Lead → Founder → Publish
- **Timeline:** 10-14 days total
- **Content types:** API docs, developer guides, architecture docs

---

## Publishing Guidelines

### Platform Specifications

**WordPress/Next.js:**
- Featured image: 1200x630px (Open Graph)
- Social share images auto-generated from featured
- Categories: Blog, Announcements, Tutorials, Use Cases
- Tags: Include business layer (Finance, Legal, etc.)

**Newsletter (ConvertKit):**
- Send time: Friday 10 AM local time
- Subject line: < 50 characters
- Preview text: Set (first 100 chars)
- Personalization: Use `{{ subscriber.first_name }}` or fallback

**Twitter/X:**
- Character limit: 280 (but keep to 250 for RT space)
- Images: 1200x675px (2:1.67 ratio)
- Threads: Number tweets (1/8, 2/8, etc.)
- Tags: @mekongmind, relevant founders when mentioned

**LinkedIn:**
- Image: 1200x627px (1.91:1 ratio)
- Tag relevant companies/people
- Use 3-5 hashtags (mix of branded and topical)
- Post time: Tuesday/Wednesday/Thursday 8-10 AM

**YouTube:**
- Title: < 60 characters (mobile display)
- Description: Include links at top (newsletter, website)
- Tags: 5-10 relevant tags
- Thumbnail: 1280x720px, high contrast, readable text
- End screen: Link to subscribe + related video

---

## Repurposing Guidelines

### From Blog to Social
- Extract 5-10 quotable lines for Twitter
- Create LinkedIn article (slightly edited)
- Make 3-5 quote graphics for Instagram
- Pull statistics/data for infographic

### From Video to Blog
- Transcribe with Descript
- Edit transcript into blog format
- Add screenshots from video
- Embed video at top

### From Newsletter to Blog
- Expand newsletter highlights into full posts
- Compile 4-5 newsletters into "Monthly Roundup" post
- Turn Q&A into standalone FAQ post

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-06-20 | Initial SOP | Content Lead |

---

*Questions? Contact: content@mekongmind.com*
