# ReviewTrust

An AI-powered business recommendation platform that retrieves live Google Maps reviews, evaluates review quality, performs semantic retrieval using Retrieval-Augmented Generation (RAG), and generates evidence-backed business recommendations using a multi-agent workflow.

Instead of relying solely on ratings or keyword matching, ReviewTrust combines live review retrieval, review quality analysis, semantic search, and LLM-powered summarization to produce transparent recommendations with confidence scores and supporting evidence.

---

# Features

- Live Google Maps business search using SerpAPI
- Automatic ingestion of recent reviews
- Review deduplication and persistent PostgreSQL storage
- Multi-agent workflow built with LangGraph
- Semantic retrieval using Amazon Titan Embeddings
- Vector search using Pinecone
- AI-generated recommendation summaries using Amazon Bedrock
- Confidence-aware recommendation ranking
- Dockerized application
- Cloud-native deployment on Amazon ECS Fargate

---

# Architecture

```
                        User
                          │
                          ▼
                  FastAPI / NiceGUI
                          │
                          ▼
                Coordinator Agent
                          │
      ┌───────────────────┼────────────────────┐
      ▼                   ▼                    ▼
Business Search     Review Retrieval     Database Lookup
      │                   │
      └──────────────┬────┘
                     ▼
           Review Quality Agent
                     │
                     ▼
         Amazon Titan Embeddings
                     │
                     ▼
               Pinecone Vector DB
                     │
                     ▼
              Summary Agent
                     │
                     ▼
             Recommendation Ranking
                     │
                     ▼
                   Response
```

---

# Agent Workflow

The application is orchestrated using LangGraph.

## Coordinator Agent

Responsible for managing the overall recommendation workflow.

It coordinates every stage of the recommendation pipeline.

---

## Business Retrieval

Searches the local PostgreSQL database for businesses.

If insufficient businesses exist, new businesses are retrieved from Google Maps using SerpAPI and stored locally.

---

## Review Retrieval

Retrieves existing reviews from PostgreSQL.

If reviews are outdated or insufficient:

- Google Maps reviews are fetched
- duplicate reviews are removed
- new reviews are inserted into PostgreSQL

---

## Review Quality Agent

Each review is evaluated using Amazon Bedrock.

The agent scores:

- Specificity
- Experience
- Relevance
- Clarity

These scores become part of the recommendation weight.

---

## Embedding Agent

Each review is converted into embeddings using

**Amazon Titan Embeddings**

Embeddings are stored in Pinecone.

---

## Semantic Retrieval

When the user provides a description like

> "good equipment and low crowding"

the description is embedded and Pinecone retrieves only the semantically relevant reviews.

---

## Summary Agent

Uses Amazon Bedrock to generate:

- recommendation summary
- positive themes
- negative themes
- confidence statement
- limitations

---

## Ranking

Businesses are ranked using

- semantic similarity
- weighted rating
- review quality
- review independence
- review recency
- evidence volume

---

# Tech Stack

## Backend

- Python
- FastAPI
- NiceGUI

## AI

- LangGraph
- LangChain
- Amazon Bedrock
- Amazon Titan Embeddings

## Vector Database

- Pinecone

## Database

- PostgreSQL
- SQLAlchemy

## External APIs

- SerpAPI

## Cloud

- Amazon ECS Fargate
- Amazon ECR
- Amazon RDS
- AWS Secrets Manager
- IAM

## DevOps

- Docker

---

# Project Structure

```
app/
│
├── agents/
│   ├── coordinator.py
│   ├── review_quality_agent.py
│   └── summary_agent.py
│
├── database/
│   ├── models.py
│   └── session.py
│
├── rag/
│   ├── embeddings.py
│   └── pinecone.py
│
├── tools/
│   ├── database_tool.py
│   ├── internet_tool.py
│   └── scoring_tool.py
│
├── ui/
│   └── home.py
│
├── workflow.py
├── config.py
└── main.py
```

---

# Running Locally

## Install dependencies

```bash
uv sync
```

---

## Environment Variables

Create

```
.env
```

```
DATABASE_URL=

AWS_REGION=

SERPAPI_API_KEY=

PINECONE_API_KEY=

PINECONE_INDEX_NAME=
```

---

## Start

```
uv run python main.py
```

---

# Docker

Build

```bash
docker build -t review-trust-system .
```

Run

```bash
docker run \
-p 8000:8080 \
--env-file .env \
review-trust-system
```

---

# AWS Deployment

The application is deployed using

- Docker
- Amazon ECS Fargate
- Amazon ECR
- Amazon RDS PostgreSQL
- AWS Secrets Manager

Application secrets are injected into the container at runtime through ECS task definitions.

---

# Recommendation Pipeline

```
User Query
      │
      ▼
Retrieve Businesses
      │
      ▼
Retrieve Reviews
      │
      ▼
Fetch Missing Reviews
      │
      ▼
Review Quality Analysis
      │
      ▼
Embedding Generation
      │
      ▼
Semantic Retrieval
      │
      ▼
LLM Summary
      │
      ▼
Weighted Ranking
      │
      ▼
Response
```

# Motivation

Most review platforms rely heavily on star ratings or keyword matching, often overlooking review credibility, recency, and contextual relevance.

ReviewTrust combines live review retrieval, semantic search, review quality assessment, and large language models to generate transparent recommendations that explain not only **what** is recommended, but also **why**.