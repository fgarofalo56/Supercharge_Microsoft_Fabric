---
hero: assets/heroes/getting-started.svg
hero_alt: Quickstart — Data Scientist Quickstart
type: quick-start
---
# Data Scientist Quickstart

> **Last Updated**: 2026-05-05 | **Role**: Data Scientist
> **Goal**: Build, train, and deploy ML models using Fabric's integrated data science capabilities — from exploration through production serving.

---

## Persona & Typical Day

You explore data, build predictive models, run experiments, and deploy trained models to production endpoints. A typical day involves querying Lakehouse tables with Spark, running feature engineering notebooks, training models with AutoML or Spark ML, evaluating experiment metrics, and collaborating with data engineers to get the right features into gold tables.

You care about reproducibility, experiment tracking, model accuracy, feature quality, and being able to iterate quickly without managing infrastructure.

---

## Your First 30 Minutes

Follow these steps to train and evaluate your first model in Fabric:

1. **Set up your workspace and Lakehouses** - Ensure you have access to bronze/silver/gold tables that contain training data.
   [:octicons-arrow-right-24: Tutorial 00: Environment Setup](../tutorials/00-environment-setup/README.md)

2. **Explore gold-layer features** - Review existing gold tables and understand the data available for modeling.
   [:octicons-arrow-right-24: Tutorial 03: Gold Layer](../tutorials/03-gold-layer/README.md)

3. **Run an AutoML experiment** - Use Fabric's AutoML to automatically train and compare models on a forecasting or classification task.
   [:octicons-arrow-right-24: AutoML & Model Endpoints](../features/automl-model-endpoints.md)

4. **Explore Semantic Link** - Use Semantic Link to bridge Power BI semantic models and Spark notebooks for integrated analysis.
   [:octicons-arrow-right-24: Semantic Link](../features/semantic-link.md)

5. **Try AI Functions for compliance scoring** - See how AI Functions can enrich data with LLM-powered transformations inline in Spark.
   [:octicons-arrow-right-24: Tutorial 09: Advanced AI/ML](../tutorials/09-advanced-ai-ml/README.md)

---

## Your First Week

| Day | Focus | Resource |
|-----|-------|----------|
| 1 | Complete 30-minute path above | Tutorials 00, 03, 09 + AutoML docs |
| 2 | Build a churn prediction model with Spark ML | [ML Notebook: Player Churn](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/notebooks/ml/01_ml_player_churn_prediction.py) |
| 3 | Set up the Feature Store for reusable features | [Feature Store Guide](../best-practices/feature-store-onelake.md) |
| 4 | Implement vector search with Eventhouse | [Vector Database](../features/eventhouse-vector-database.md) |
| 5 | Deploy a model and configure drift detection | [MLOps Production Guide](../best-practices/mlops-fabric-production.md) |

---

## Key Features for Data Scientists

| Feature | Doc Link | Why It Matters |
|---------|----------|----------------|
| AutoML & Model Endpoints | [AutoML Guide](../features/automl-model-endpoints.md) | Rapid model training with automatic algorithm selection and hyperparameter tuning |
| Semantic Link | [Semantic Link](../features/semantic-link.md) | Bridge Power BI models and Spark notebooks - query semantic models from Python |
| Vector Database (Eventhouse) | [Vector DB Guide](../features/eventhouse-vector-database.md) | Store and search embeddings for RAG, similarity search, and recommendation systems |
| AI Functions | [AI Copilot](../features/ai-copilot-configuration.md) | LLM-powered inline data transformations in Spark notebooks |
| Feature Store | [Feature Store](../best-practices/feature-store-onelake.md) | Centralized, versioned feature management for consistent model training |
| MLOps Production | [MLOps Guide](../best-practices/mlops-fabric-production.md) | Model registry, deployment, A/B testing, and production monitoring |
| Drift Detection | [Drift Detection](../best-practices/model-monitoring-drift-detection.md) | Detect when production data distribution shifts from training data |
| Responsible AI | [Responsible AI](../best-practices/responsible-ai-framework.md) | Fairness, explainability, and bias detection frameworks |
| RAG Patterns | [RAG Deep Dive](../features/rag-patterns-deep-dive.md) | Retrieval-augmented generation patterns for knowledge-grounded AI |
| Prompt Engineering | [Prompt Engineering](../features/prompt-engineering-fabric.md) | Best practices for working with LLMs in Fabric notebooks |

---

## Common Pitfalls

1. **Training on raw Bronze data** - Bronze tables contain duplicates, nulls, and schema inconsistencies. Always train on validated Silver or curated Gold tables.

2. **Skipping experiment tracking** - Without tracking metrics, parameters, and artifacts, you cannot reproduce results or compare runs. Use MLflow experiment tracking built into Fabric.

3. **Building features in notebooks instead of the Feature Store** - Ad-hoc feature engineering in notebooks leads to training/serving skew. Use the Feature Store for consistent, reusable features across training and inference.

4. **Ignoring model drift after deployment** - A model that was accurate at training time degrades as real-world data distributions shift. Set up drift detection monitoring from day one. See the [Drift Detection Guide](../best-practices/model-monitoring-drift-detection.md).

5. **Not leveraging Semantic Link** - Many data scientists query raw tables when the semantic model already has the right business logic (measures, relationships). Semantic Link lets you use those definitions directly in Spark.

---

## Related Resources

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } __AutoML & Model Endpoints__

    ---

    Automated model training, comparison, and deployment to real-time scoring endpoints.

    [:octicons-arrow-right-24: AutoML Guide](../features/automl-model-endpoints.md)

-   :material-vector-point:{ .lg .middle } __Vector Database__

    ---

    Eventhouse-based vector storage for embeddings, similarity search, and RAG applications.

    [:octicons-arrow-right-24: Vector DB Guide](../features/eventhouse-vector-database.md)

-   :material-factory:{ .lg .middle } __MLOps Production__

    ---

    End-to-end ML lifecycle management from experiment to production serving.

    [:octicons-arrow-right-24: MLOps Guide](../best-practices/mlops-fabric-production.md)

-   :material-brain:{ .lg .middle } __RAG Patterns__

    ---

    Retrieval-augmented generation architectures using Fabric's data and compute.

    [:octicons-arrow-right-24: RAG Deep Dive](../features/rag-patterns-deep-dive.md)

</div>
