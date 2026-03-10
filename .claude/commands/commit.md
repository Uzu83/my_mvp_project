---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Conventional Commitsフォーマットでgit commitを作成する
---

## Context
- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task
変更内容を分析し、Conventional Commits形式の
適切な英語コミットメッセージを作成してgit commitを実行せよ。
未追跡の変更があればgit addしてからcommitすること。
