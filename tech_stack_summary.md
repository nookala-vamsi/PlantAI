# PlantGuard AI — Technology Stack Summary

A concise overview of the complete frontend, backend, database, and machine learning technology stack powering the PlantGuard AI suite.

---

## 📱 1. Mobile Frontend
Built as a premium, highly responsive Material 3 mobile application.
- **Framework**: Flutter SDK (v3.11.1+)
- **State Management**: Flutter Riverpod (v2.5.0) — reactive, asynchronous data flow
- **Navigation Routing**: GoRouter (v14.0.0) — declarative multi-screen navigation
- **API Networking**: Dio (v5.4.0) — asynchronous REST client with interceptors
- **Core Dependencies**:
  - `image_picker` (v1.1.0) — native camera & gallery uploads
  - `shimmer` (v3.0.0) — frosted-glass loader placeholders
  - `intl` (v0.19.0) — local timezone conversion & formatting (IST)
  - `lottie` (v3.1.0) — interactive micro-animations

---

## ⚡ 2. Backend Service
High-performance asynchronous API service processing prediction requests in real-time.
- **Runtime**: Python (v3.10+)
- **Web Framework**: FastAPI (v0.100+) — async ASGI web framework
- **Server Gateway**: Uvicorn (v0.22+) — high-speed ASGI server
- **Database ORM**: SQLAlchemy 2.0 (with `asyncpg` async PostgreSQL driver)
- **Database Migrations**: Alembic — automated, versioned schema management
- **Caches & Rate Limits**: Redis (v7-alpine) — jwt blacklists and rate limiting
- **Image Cloud Storage**: MinIO — S3-compatible local object storage

---

## 🧠 3. Machine Learning Models
Two distinct cutting-edge AI architectures deployed inside the backend prediction pipelines.

### Module A: Plant Disease Classifier (CNN 3-Gate Pipeline)
- **Task**: 38-class diagnostic disease classification across 14 unique crops
- **Frameworks**: TensorFlow (v2.12+), Keras, NumPy, Pillow (image preprocessing)
- **Architecture**: 3-Gate sequential filtering pipeline powered by deep CNNs:
  - **Gate 1**: Leaf vs Non-Leaf Detector (Binary Classifier)
  - **Gate 2**: Plant Species Classifier (14 distinct crop species)
  - **Gate 3**: Disease Classifier (built with Keras **EfficientNet** feature extractors)
- **Dataset**: Trained on the New Plant Diseases Dataset (enriched leaf disease images)

### Module B: Natural Drug Origin Classifier (GIN - Graph Isomorphism Network)
- **Task**: 3-class compound biological origin prediction (Plant, Fungal, Bacterial)
- **Frameworks**: PyTorch (v2.0+), PyTorch Geometric (PyG), RDKit (SMILES molecular parsing & graph generation)
- **Architecture**: Pure Graph Isomorphism Network (GIN) processing molecular graphs:
  - **Atom Featurization (Nodes)**: 74-dimensional one-hot encoded node feature vectors.
  - **Bond Featurization (Edges)**: 12-dimensional one-hot encoded edge feature vectors.
  - **Message Passing**: `GINEConv` convolutions (3 layers) with internal MLPs utilizing bond features.
  - **Readout (Pooling)**: Global sum-pooling layer to synthesize molecular-level embeddings (128-dimensional).
  - **Classification Head**: Fully Connected MLP (Linear → ReLU → Dropout → Linear) outputting 3 biological origin probabilities.
- **Dataset**: Trained on the COCONUT database (61,037 natural drug compounds)
