# CertCoach

An adaptive exam preparation platform that uses blueprint-driven study planning, spaced repetition, and AI-powered practice sessions to help professionals master technical certifications.

## 🎯 Product Vision

CertCoach transforms exam preparation through four core pillars:

1. **Blueprint-first Study Planner** - Plans based on official exam weights, auto-reschedules on slips, exports to calendar
2. **Adaptive Practice Engine** - 2-3 reviews + 8-12 focus items with rationales and official documentation links  
3. **Mastery Map + Weekly Mocks** - Per-objective probability tracking with gap analysis and plan adjustments
4. **Notes → Flashcards** - One-click spaced repetition system from your own study notes

## 🏗 Architecture

**Monorepo Structure** (Turborepo)
- **Apps**: Next.js web app, React Native mobile app
- **Services**: 7 microservices (FastAPI) for modular functionality  
- **Packages**: Shared UI components, TypeScript configs, Python utilities
- **Data**: Exam blueprints and seed content
- **Infrastructure**: Terraform, Docker, CI/CD workflows

**Tech Stack**
- Frontend: Next.js, React Native + Expo, TypeScript
- Backend: Python FastAPI microservices
- Database: PostgreSQL + pgvector, Redis
- Observability: OpenTelemetry, Prometheus, Grafana
- Package Management: uv (Python), npm (Node.js)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- uv package manager
- PostgreSQL 15+
- Redis 7+

### Development Setup

1. **Clone and install dependencies**
   ```bash
   git clone https://github.com/aiden-krain/certcoach.git
   cd certcoach
   
   # Install Node.js dependencies
   npm install
   
   # Install Python dependencies with uv
   uv sync --dev
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development servers**
   ```bash
   # Start all services in development mode
   npm run dev
   
   # Or start specific services
   turbo dev --filter=web
   turbo dev --filter=api-gateway
   ```

## 📁 Project Structure

```
certcoach/
├─ apps/
│  ├─ web/                    # Next.js web application
│  └─ mobile/                 # React Native + Expo mobile app
├─ services/
│  ├─ api-gateway/            # FastAPI gateway, auth, routing
│  ├─ planner/                # Study planning service
│  ├─ practice-engine/        # Session assembly and grading
│  ├─ item-factory/           # AI-powered item generation
│  ├─ mastery-srs/            # Mastery tracking + spaced repetition
│  ├─ explain-rag/            # Documentation anchors + citations
│  └─ telemetry/              # Analytics and reweighting
├─ packages/
│  ├─ ui/                     # Shared React components
│  ├─ ts-config/              # Shared TypeScript configuration
│  ├─ python-common/          # Shared Python utilities
│  └─ schemas/                # OpenAPI and JSON schemas
├─ data/
│  ├─ blueprints/             # Exam blueprints (DP-700, DBX-DEA)
│  └─ seeds/                  # Starter items and challenge sets
├─ infra/                     # Infrastructure as code
├─ scripts/                   # Utility scripts
└─ docs/                      # Documentation and ADRs
```

## 🎓 Supported Certifications

### Currently Available
- **DP-700**: Microsoft Fabric Data Engineer
- **Databricks Data Engineer Associate**

### Planned
- Azure Data Engineer Associate (DP-203)
- AWS Data Engineer Professional
- Google Cloud Professional Data Engineer

## 🔧 Development Commands

```bash
# Development
npm run dev              # Start all development servers
npm run build           # Build all applications
npm run test            # Run all tests
npm run lint            # Lint all code
npm run type-check      # TypeScript type checking

# Python services
uv run alembic upgrade head    # Run database migrations
uv run pytest                 # Run Python tests
uv run mypy .                  # Type check Python code

# Individual services
turbo dev --filter=web         # Start web app only
turbo build --filter=mobile    # Build mobile app only
```

## 🧪 Testing

- **Unit Tests**: Jest (TypeScript), pytest (Python)
- **Integration Tests**: Automated API testing with test databases
- **E2E Tests**: Playwright for critical user journeys
- **Load Tests**: k6 for performance validation

## 📊 Monitoring & Observability

- **Metrics**: Prometheus + Grafana dashboards
- **Tracing**: OpenTelemetry distributed tracing
- **Logs**: Structured logging with correlation IDs
- **Alerts**: Critical path SLO monitoring

## 🛡 Security & Compliance

- **Authentication**: JWT + OAuth (GitHub/Microsoft)
- **Authorization**: Row-level security with user isolation
- **Data Privacy**: GDPR/CCPA compliant data handling
- **Content**: Licensed documentation only, provenance tracking
- **Infrastructure**: Encrypted at rest, secrets management

## 📈 Performance Targets

- Session assembly: < 700ms (p95)
- Weekly mock grading: < 3s
- Mobile drill loading: < 300ms
- API response times: < 200ms (p95)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/aiden-krain/certcoach/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aiden-krain/certcoach/discussions)

---

**Note**: This is an MVP implementation focusing on DP-700 and Databricks Data Engineer Associate certifications. The architecture is designed to scale to additional certifications and advanced features.
