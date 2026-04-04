---
name: smart-explore
description: "Progressive code exploration — structure first, drill second. Reduces code reading from 10-15k tokens per file to 200-500 tokens."
---

# Smart Explore — Progressive Code Exploration

> Read code structure before reading code. Show function signatures and types first, then drill into specific functions only when needed.

## When to Use

| Signal | Use smart-explore | Use standard Read |
|--------|-------------------|-------------------|
| "Understand this module/feature" | Yes | No |
| Exploring unfamiliar codebase | Yes | No |
| Finding where to add a feature | Yes | No |
| Need to read one specific function | No | Yes |
| Debugging a known line | No | Yes |
| File is < 100 lines | No | Yes (just read it) |

**Don't use for**: small projects (< 20 files), single-file tasks, or when you already know what to read.

## Protocol

When asked to explore a codebase or understand a module:

### 1. Structure first

Use Grep to find function/class definitions:

**TypeScript/JavaScript/React:**
```
rg "^\s*(export\s+)?(async\s+)?(function|class|const|let|interface|type)\s+\w+" src/ --no-heading -n
```

**Python:**
```
rg "^\s*(async\s+)?(def|class)\s+\w+" src/ --no-heading -n
```

**Rust:**
```
rg "^\s*(pub\s+)?(async\s+)?fn |^\s*(pub\s+)?(struct|enum|trait|impl)\s" src/ --no-heading -n
```

Use `^\s*` not `^` — methods inside class bodies and impl blocks are indented. The `^` pattern misses ~70% of methods.

### 2. Identify relevant symbols

Based on names, pick 2-3 functions/classes to read.

### 3. Targeted read

Use Read with offset/limit to read specific functions — not the whole file.

### 4. Cross-reference (only if needed)

Use Grep to find callers: `rg "functionName" --type ts -n`

**Never read a file start-to-finish when exploring. Always structure first.**

## Workflow Examples

### Understand an unfamiliar module

**Without smart-explore** (~18k tokens):
```
Read src/payments/processor.ts   # 400 lines
Read src/payments/validator.ts   # 300 lines
Read src/payments/gateway.ts     # 500 lines
Read src/payments/types.ts       # 200 lines
```

**With smart-explore** (~2.5k tokens):
```
# Step 1: Get structure (~400 tokens for all 4 files)
rg "^\s*(export\s+)?(async\s+)?(function|class|const|interface|type)\s+\w+" src/payments/ -n

# Step 2: Identify what matters from signatures
# "processPayment() calls validateAmount() — read those two"

# Step 3: Read only those functions (with line offsets)
Read src/payments/processor.ts (lines 45-90)   # ~300 tokens
Read src/payments/validator.ts (lines 12-40)   # ~200 tokens
```

### Find where to add a feature

```
# Goal: Add rate limiting to the auth service
# Step 1: What's in the auth module?
rg "^\s*(export\s+)?(async\s+)?(function|class|const)\s+\w+" src/auth/ -n

# Output:
#   src/auth/middleware.ts:15:export async function authenticate(req: Request)
#   src/auth/middleware.ts:45:export async function refreshToken(token: string)
#   src/auth/service.ts:8:export function validate(claims: Claims)
#   src/auth/service.ts:20:export async function login(creds: Credentials)

# Step 2: Rate limiting goes in middleware.ts before authenticate()
# Read ONLY the authenticate function
Read src/auth/middleware.ts lines 15-44

# Step 3: Add feature — done
```

## Token Benchmarks

| Operation | Without | With | Savings |
|---|---|---|---|
| Understand 5-file module | ~18,000 tokens | ~2,500 tokens | ~86% |
| Find where to add a feature | ~8,000 tokens | ~800 tokens | ~90% |
| PR review (10 changed files) | ~25,000 tokens | ~3,500 tokens | ~86% |
| Single function lookup | ~3,000 tokens | ~350 tokens | ~88% |

## Advanced: tree-sitter CLI

For larger codebases, install tree-sitter CLI for AST-based extraction:

```bash
brew install tree-sitter
```

See the full extract-signatures.py script in the [claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/examples/skills/smart-explore.md) for a Python script that extracts signatures automatically.

## Advanced: MCP Servers

For codebases over 50 files, consider an indexed MCP server:

| Use Case | Recommended |
|---|---|
| General code exploration | `mcp-server-tree-sitter` |
| PR code reviews | `code-review-graph` |
| Symbol-heavy workflows | `jCodeMunch` (non-commercial) |

## Gotchas
