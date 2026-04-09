# BatchSystem Naming Conventions

## Resource Naming

| Resource | Format | Example |
|----------|--------|---------|
| CronWorkflow | `{team}-{jobName}-sj` | `rd3-retry-writeoff-job-sj` |
| WorkflowTemplate | `{team}-{project}-argojob-wt` | `rd3-jkopay-insurance-argojob-wt` |
| `batchsystem/project` annotation | project name | `jkopay-insurance` |
| `templateName` param | `{env}-{team}-{project}-argojob-wt` (prod: no env) | `sit-rd3-jkopay-insurance-argojob-wt` |
| `jobData.jobName` | all lowercase (= DI serviceKey) | `retrywriteoffjob` |
| ServiceAccount | `{team}-batchsystem-sa` | `rd3-batchsystem-sa` |
| K8s Secret (SIT/UAT) | `{env}-{project}-secret` | `sit-jkopay-insurance-secret` |
| Image path | `{registry}/{team}/{project}/{env}/argojob:{hash}` | — |
| Shared template | `batchsystem-main-cron-workflow-template` | — |
| Shared template (sharding) | `batchsystem-main-cron-workflow-template-sharding` | — |

## Environment Prefix Rules

| Environment | Prefix | Example |
|-------------|--------|---------|
| SIT | `sit-` | `sit-rd3-jkopay-insurance-argojob-wt` |
| UAT | `uat-` | `uat-rd3-jkopay-insurance-argojob-wt` |
| PROD | (none) | `rd3-jkopay-insurance-argojob-wt` |

## Schedule Syntax (Asia/Taipei)

```
分 時 日 月 週
30 4 * * *        每天 04:30
0 10 * * *        每天 10:00
0 8 1 * *         每月 1 號 08:00
*/30 * * * *      每 30 分鐘
20 0 * * *        每天 00:20
```

## Image Registry

```
asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository/{team}/{project}/{env}/argojob:{git-commit-hash}
```

## Vault Path (PROD)

```
secret/data/prod/{team}/app/{project}
```

## GitOps Directory Structure

```
gitops/{team}/{project}/kustomize/
├── base/
│   ├── jobs/
│   │   ├── {team}-{project}-argojob-wt.yaml
│   │   └── {team}-{jobName}-sj.yaml
│   └── kustomization.yaml
└── overlays/
    └── {env}/idc/
        ├── jobs/*.patch.yaml
        ├── kustomization.yaml
        └── kustomconfig.yaml
```
