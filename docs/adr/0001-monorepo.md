# ADR 0001: Monorepo Architecture with Turborepo

**Status**: Accepted  
**Date**: 2024-12-01  
**Authors**: CertCoach Engineering Team  
**Reviewers**: Architecture Review Board  

## Context

CertCoach is building an adaptive exam preparation platform with multiple client applications (web, mobile) and several backend microservices. We need to decide on the code organization strategy that will:

1. Enable efficient development and deployment workflows
2. Facilitate code sharing between frontend and backend components
3. Support independent service development while maintaining consistency
4. Provide clear dependency management and build optimization
5. Scale effectively as the team and codebase grow

## Decision Drivers

### Technical Requirements
- **Multi-platform Development**: Next.js web app + React Native mobile app
- **Microservices Architecture**: 7 distinct backend services with FastAPI
- **Shared Components**: UI components, TypeScript types, Python utilities
- **Independent Deployments**: Services must be deployable independently
- **Development Velocity**: Fast local development and CI/CD pipelines

### Team Considerations
- Mixed frontend/backend development team
- Need for clear ownership boundaries
- Desire for consistent tooling and standards
- Plans for rapid team scaling

### Alternatives Considered

#### Option 1: Polyrepo (Multiple Repositories)
```
certcoach-web/          (Next.js)
certcoach-mobile/       (React Native)
certcoach-api-gateway/  (FastAPI)
certcoach-planner/      (FastAPI)
certcoach-practice/     (FastAPI)
... (separate repo for each service)
```

**Pros**:
- Clear service boundaries and ownership
- Independent release cycles
- Technology-specific tooling
- Smaller repository sizes

**Cons**:
- Code duplication across repositories
- Complex dependency management
- Difficult cross-service refactoring
- Inconsistent tooling and standards
- Higher maintenance overhead

#### Option 2: Monolith Repository
```
certcoach/
├── frontend/web/
├── frontend/mobile/
├── backend/
│   ├── gateway/
│   ├── planner/
│   └── practice/
└── shared/
```

**Pros**:
- Simplified dependency management
- Easy code sharing
- Consistent tooling
- Atomic cross-service changes

**Cons**:
- Potential coupling between services
- Larger repository size
- Complex CI/CD for selective deployments
- Risk of monolithic thinking

#### Option 3: Monorepo with Turborepo (Selected)
```
certcoach/
├── apps/
│   ├── web/           (Next.js)
│   └── mobile/        (React Native)
├── services/
│   ├── api-gateway/   (FastAPI)
│   ├── planner/       (FastAPI)
│   └── practice/      (FastAPI)
├── packages/
│   ├── ui/            (Shared React components)
│   ├── types/         (TypeScript definitions)
│   └── python-common/ (Python utilities)
└── tools/
    ├── eslint-config/
    └── tsconfig/
```

## Decision

We will use **Option 3: Monorepo with Turborepo** for the following reasons:

### Benefits

#### 1. Optimized Build Pipeline
```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "test": {
      "dependsOn": ["^build"]
    }
  }
}
```
Turborepo provides intelligent task scheduling and caching, building only what changed.

#### 2. Effective Code Sharing
- **Frontend**: Shared React components between web and mobile
- **Backend**: Common Python utilities for authentication, database, etc.
- **Types**: Shared TypeScript interfaces and API schemas
- **Tooling**: Consistent linting, formatting, and build configurations

#### 3. Developer Experience
- Single repository to clone and understand
- Unified development scripts (`npm run dev` starts everything)
- Consistent tooling across all projects
- Simplified dependency management

#### 4. CI/CD Optimization
- Incremental builds based on changed packages
- Intelligent test execution (only test affected code)
- Parallel pipeline execution
- Selective deployment triggers

#### 5. Refactoring and Maintenance
- Atomic changes across multiple services
- Easy large-scale refactoring with IDE support
- Consistent version management
- Simplified dependency updates

### Implementation Strategy

#### Phase 1: Core Structure (Week 1)
1. Initialize Turborepo workspace
2. Set up basic apps (web, mobile) and services
3. Configure shared packages (ui, types, python-common)
4. Establish linting and formatting standards

#### Phase 2: Build Pipeline (Week 2)
1. Configure Turborepo tasks and dependencies
2. Set up CI/CD with change detection
3. Implement caching strategies
4. Configure deployment pipelines

#### Phase 3: Developer Tooling (Week 3)
1. IDE configuration and recommendations
2. Development environment setup scripts
3. Documentation and contribution guides
4. Local development optimization

### Trade-offs Accepted

#### Repository Size
- **Trade-off**: Larger repository with all code
- **Mitigation**: Git LFS for large assets, shallow clones for CI

#### Coordination Overhead
- **Trade-off**: Need for coordination on shared packages
- **Mitigation**: Clear ownership model, automated testing, semantic versioning

#### Tool Complexity
- **Trade-off**: Turborepo learning curve and configuration
- **Mitigation**: Comprehensive documentation, team training, gradual adoption

## Implementation Details

### Directory Structure
```
certcoach/
├── apps/
│   ├── web/                    # Next.js application
│   │   ├── package.json
│   │   ├── src/
│   │   └── public/
│   └── mobile/                 # React Native + Expo
│       ├── package.json
│       ├── src/
│       └── assets/
├── services/
│   ├── api-gateway/            # FastAPI gateway service
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   └── tests/
│   ├── planner/                # Study planning service
│   ├── practice-engine/        # Practice session service
│   ├── item-factory/           # Content generation service
│   ├── mastery-srs/           # Mastery tracking + SRS
│   ├── explain-rag/           # Documentation RAG service
│   └── telemetry/             # Analytics service
├── packages/
│   ├── ui/                     # Shared React components
│   │   ├── package.json
│   │   ├── src/components/
│   │   └── src/hooks/
│   ├── ts-config/              # Shared TypeScript configs
│   ├── python-common/          # Shared Python utilities
│   │   ├── pyproject.toml
│   │   ├── src/auth/
│   │   ├── src/database/
│   │   └── src/models/
│   └── schemas/                # API schemas and types
├── data/                       # Static data and configuration
├── infra/                      # Infrastructure as code
├── scripts/                    # Utility scripts
├── package.json                # Root workspace configuration
├── pyproject.toml             # Python workspace configuration
└── turbo.json                 # Turborepo configuration
```

### Turborepo Configuration
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

### Package Dependencies
```json
{
  "name": "certcoach",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "build": "turbo build",
    "dev": "turbo dev",
    "lint": "turbo lint",
    "test": "turbo test"
  }
}
```

## Consequences

### Positive
1. **Faster Development**: Shared components and utilities reduce duplication
2. **Better Testing**: Atomic changes enable comprehensive testing
3. **Improved Consistency**: Shared tooling ensures consistent code quality
4. **Efficient CI/CD**: Intelligent caching and incremental builds
5. **Easier Onboarding**: Single repository with clear structure

### Negative
1. **Learning Curve**: Team needs to learn Turborepo concepts
2. **Initial Complexity**: More upfront configuration than simple approaches
3. **Repository Size**: Larger repository may impact some operations
4. **Coordination Need**: Changes to shared packages require coordination

### Neutral
1. **Tool Dependency**: Reliance on Turborepo ecosystem
2. **Build Complexity**: More sophisticated build pipeline
3. **IDE Performance**: May require optimization for large repository

## Monitoring and Review

### Success Metrics
- **Build Time**: Target <5 minutes for full build, <2 minutes incremental
- **Development Velocity**: Measure feature delivery speed
- **Code Reuse**: Track shared package adoption
- **Developer Satisfaction**: Regular team feedback on developer experience

### Review Schedule
- **Monthly**: Performance metrics review
- **Quarterly**: Developer experience survey
- **Bi-annually**: Architecture decision review
- **As needed**: When significant pain points emerge

### Decision Review Triggers
1. Build times consistently exceed targets
2. Developer satisfaction scores drop significantly
3. Repository size impacts become problematic
4. Team structure changes significantly
5. Technology landscape shifts (e.g., better alternatives emerge)

## Related Decisions
- [ADR 0002: Microservices Communication Patterns](./0002-microservices-communication.md) (planned)
- [ADR 0003: Frontend State Management](./0003-frontend-state-management.md) (planned)
- [ADR 0004: Database Architecture](./0004-database-architecture.md) (planned)

## References
- [Turborepo Documentation](https://turbo.build/repo/docs)
- [Monorepo Best Practices](https://monorepo.tools/)
- [Google's Monorepo Experience](https://research.google/pubs/pub45424/)
- [Nx vs Turborepo Comparison](https://blog.nrwl.io/turborepo-vs-nx-a-brief-comparison-5c2dd7e5e0c6)

---
**Last Updated**: 2024-12-01  
**Next Review**: 2025-03-01
