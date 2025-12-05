#!/bin/bash

# 🔍 Agent Quality Check Script
# Verifies all agents are running correctly and communicating

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 ARCHON AGENT QUALITY CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Check all agents are running
echo "Test 1: Checking agent status..."
RUNNING=$(docker ps --filter "name=agent" --filter "status=running" -q | wc -l | tr -d ' ')
EXPECTED=7

if [ "$RUNNING" -eq "$EXPECTED" ]; then
    echo "✅ PASS: All $EXPECTED agents are running"
else
    echo "❌ FAIL: Only $RUNNING/$EXPECTED agents running"
    docker ps -a --filter "name=agent" --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Test 2: Check for startup messages
echo ""
echo "Test 2: Checking agent initialization logs..."
INIT_SUCCESS=0

for agent in testing data devex documentation ui infrastructure orchestration; do
    LOG=$(docker logs archon-agent-$agent 2>&1 || true)
    
    if echo "$LOG" | grep -q "Agent initialized"; then
        echo "✅ $agent: Successfully initialized"
        ((INIT_SUCCESS++))
    else
        echo "❌ $agent: No initialization message found"
    fi
done

if [ "$INIT_SUCCESS" -eq 7 ]; then
    echo "✅ PASS: All agents initialized successfully"
else
    echo "⚠️  WARNING: $INIT_SUCCESS/7 agents initialized"
fi

# Test 3: Check Redis connectivity
echo ""
echo "Test 3: Checking Redis connectivity..."
REDIS_PING=$(docker exec archon-redis redis-cli ping 2>/dev/null || echo "FAILED")

if [ "$REDIS_PING" == "PONG" ]; then
    echo "✅ PASS: Redis is responsive"
else
    echo "❌ FAIL: Redis not responding"
    exit 1
fi

# Test 4: Check Postgres connectivity
echo ""
echo "Test 4: Checking Postgres connectivity..."
PG_CHECK=$(docker exec archon-postgres pg_isready -U archon 2>/dev/null || echo "FAILED")

if echo "$PG_CHECK" | grep -q "accepting connections"; then
    echo "✅ PASS: Postgres is accepting connections"
else
    echo "❌ FAIL: Postgres not ready"
    exit 1
fi

# Test 5: Check for errors in logs
echo ""
echo "Test 5: Scanning for errors in agent logs..."
ERROR_COUNT=0

for agent in testing data devex documentation ui infrastructure orchestration; do
    ERRORS=$(docker logs archon-agent-$agent 2>&1 | grep -i "error\|exception\|failed\|traceback" | grep -v "ERROR_THRESHOLD" | wc -l | tr -d ' ')
    
    if [ "$ERRORS" -gt 0 ]; then
        echo "⚠️  $agent: Found $ERRORS potential errors"
        ((ERROR_COUNT++))
    else
        echo "✅ $agent: No errors detected"
    fi
done

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ PASS: No errors detected in logs"
else
    echo "⚠️  WARNING: Errors detected in $ERROR_COUNT agent(s)"
    echo "   Review logs with: docker compose -f docker-compose.agents.yml logs"
fi

# Test 6: Check EventBus subscriptions
echo ""
echo "Test 6: Checking EventBus subscriptions (Redis pub/sub)..."
NUMPAT=$(docker exec archon-redis redis-cli PUBSUB NUMPAT 2>/dev/null || echo "0")

if [ "$NUMPAT" -gt 0 ]; then
    echo "✅ PASS: $NUMPAT pattern subscriptions active"
else
    echo "⚠️  WARNING: No active subscriptions detected"
    echo "   Agents may not be listening to events yet"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 QUALITY CHECK SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Agents Running:        $RUNNING / $EXPECTED"
echo "Agents Initialized:    $INIT_SUCCESS / 7"
echo "Redis:                 $([ "$REDIS_PING" == "PONG" ] && echo "✅ OK" || echo "❌ FAIL")"
echo "Postgres:              $(echo "$PG_CHECK" | grep -q "accepting" && echo "✅ OK" || echo "❌ FAIL")"
echo "Errors Detected:       $ERROR_COUNT agents"
echo "EventBus Subscribers:  $NUMPAT"
echo ""

if [ "$RUNNING" -eq 7 ] && [ "$ERROR_COUNT" -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 ALL QUALITY CHECKS PASSED!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ System is ready for Phase 2 (Agent Communication Testing)"
    echo ""
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  SOME ISSUES DETECTED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Review logs and fix errors before proceeding to Phase 2"
    echo ""
    exit 1
fi
