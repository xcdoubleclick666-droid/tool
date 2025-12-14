#!/usr/bin/env bash
set -euo pipefail

# 用法：
# 1) 在本地创建并推送一个临时分支（可选，仅用于保存变更）
#    git checkout -b build-windows-$(date +%s)
#    git push origin HEAD
# 2) 导出环境变量：
#    export GITHUB_TOKEN=ghp_xxxyourtokenxxx
#    export GITHUB_OWNER=your-github-username-or-org
#    export GITHUB_REPO=your-repo-name
#    export WORKFLOW_FILE=build-windows.yml
#    export REF=main
# 3) 运行本脚本以触发 Actions workflow（需要 repo 权限的 token）

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "请先设置 GITHUB_TOKEN 环境变量（需要 repo 权限）"
  exit 1
fi
if [ -z "${GITHUB_OWNER:-}" ] || [ -z "${GITHUB_REPO:-}" ] || [ -z "${WORKFLOW_FILE:-}" ] || [ -z "${REF:-}" ]; then
  echo "请先设置 GITHUB_OWNER, GITHUB_REPO, WORKFLOW_FILE, REF 环境变量"
  echo "例如： export GITHUB_OWNER=yourname; export GITHUB_REPO=FitnessToolbox; export WORKFLOW_FILE=build-windows.yml; export REF=main"
  exit 1
fi

echo "触发 workflow ${WORKFLOW_FILE} 在 ${GITHUB_OWNER}/${GITHUB_REPO} (ref=${REF})"

API_URL="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches"

curl -s -X POST "$API_URL" \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"ref\": \"${REF}\"}"

echo "已发送 dispatch 请求。请到 GitHub Actions 页面查看运行状态并下载产物。"
