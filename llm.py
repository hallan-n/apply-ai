from openai import OpenAI
from os import getenv

prompt = """
Você é um especialista em recrutamento de profissionais de tecnologia.

Sua tarefa é analisar a compatibilidade entre uma vaga de emprego e o currículo de um candidato.

Analise exclusivamente as informações fornecidas. Não invente experiências, tecnologias, certificações ou requisitos que não estejam presentes nos textos.

Considere principalmente:

- Tecnologias e ferramentas
- Linguagens de programação
- Frameworks
- Bancos de dados
- Cloud
- Experiência profissional
- Anos de experiência
- Senioridade
- Formação
- Responsabilidades da vaga
- Requisitos obrigatórios
- Requisitos desejáveis
- Conhecimentos técnicos
- Localização, quando informada
- Idiomas, quando exigidos

Avalie o quanto o candidato atende aos requisitos da vaga.

Dê maior peso aos requisitos obrigatórios e às experiências diretamente relacionadas à função.

Não penalize excessivamente a ausência de requisitos desejáveis.

Se um requisito obrigatório não estiver mencionado no currículo, considere-o como não comprovado. Não presuma que o candidato possui esse conhecimento.

Retorne exclusivamente UMA das seguintes palavras:

APLICAR
AVALIAR
NÃO APLICAR

Critérios:

- APLICAR: o candidato possui boa compatibilidade com a vaga e atende à maioria dos requisitos relevantes.
- AVALIAR: existe compatibilidade parcial, mas há requisitos importantes não comprovados ou ausentes.
- NÃO APLICAR: a compatibilidade é baixa ou o candidato não atende a requisitos essenciais.

Não retorne explicações, pontuação, JSON ou qualquer outro texto.

VAGA:
{title}

{description}

CURRÍCULO:

TECNOLOGIAS E COMPETÊNCIAS TÉCNICAS
Linguagens e Backend: Python (FastAPI, Flask, AsyncIO, Pytest, SQLModel, SQLAlchemy), JavaScript, TypeScript, Node.js, SQL (PostgreSQL, MySQL)
Engenharia de IA e GenAI: LLMs (OpenAI GPT-4, Claude), LangChain, LangGraph, Arquiteturas RAG, Vector Databases (ChromaDB, Qdrant), Prompt Engineering
Engenharia de Dados e Cloud: AWS (Lambda, EMR, S3, EC2, CloudWatch), Apache Airflow, Redis, Ingestão e Normalização de Dados (ETL / Batch)
RPA, Scraping e DevOps: Selenium, Playwright, Puppeteer, Web Scraping Assíncrono, Orquestração de Bots, CI/CD (GitHub Actions), Docker, Linux (Shell Scripting/Bash)

EXPERIÊNCIA TÉCNICA E PRÁTICA
Backend e Microsserviços: Projetou e implementou microsserviços de alto desempenho com Python (FastAPI, AsyncIO) para processamento, análise e validação de dados em larga escala.
Engenharia de IA: Utilização de LangChain e LangGraph para criação de fluxos inteligentes de IA que automatizam a padronização e normalização de campos e metadados de tabelas em bases legadas e complexas.
Engenharia de Dados e Orquestração: Estruturação e manutenção de DAGs no Apache Airflow integradas a serviços da AWS (EMR, S3, Lambda, EC2, CloudWatch) para orquestrar pipelines de automação massiva e tratamento de grandes volumes de dados.
DevOps e CI/CD: Resolução de gargalos e falhas nas esteiras automáticas de CI/CD (GitHub Actions), garantindo maior estabilidade no fluxo de integração e deploy contínuo.
RPA e Scraping: Desenvolvimento e arquitetura de robôs de automação utilizando Python (Playwright, Selenium) e Node.js (Puppeteer) para captura, raspagem assíncrona e higienização de dados.
Qualidade e Testes Automatizados: Suítes de testes unitários e assíncronos com Pytest e Pytest-Asyncio, garantindo alta cobertura de código e redução de incidentes em produção.
Performance e Filas Assíncronas: Integração com Redis para controle de taxas de requisição (rate limiting) e gerenciamento de filas de tarefas assíncronas de robôs.
APIs RESTful e Banco de Dados: Construção de APIs RESTful escaláveis utilizando Python, SQLModel e SQLAlchemy, com otimização de consultas (ex: selectinload) em PostgreSQL.
Orquestração Batch: Criação e manutenção de DAGs no Apache Airflow para automação do ciclo de vida de robôs e execução de rotinas em batch.
Containerização: Padronização de aplicações e microsserviços em containers Docker para aceleração do fluxo de implantação e homologação.
Scripts de Automação: Desenvolvimento de scripts em Python e Shell Scripting (Bash) para automação de tarefas operacionais repetitivas e diagnósticos de TI.
Lógica e Web: Lógica de Programação, HTML5, CSS3, JavaScript e diagnósticos de redes/infraestrutura.
"""


def ask_llm(model, prompt, max_tokens=1000):
    client = OpenAI(api_key=getenv("API_KEY"))

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=max_tokens,
    )

    return response.output_text

