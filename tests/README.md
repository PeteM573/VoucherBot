# VoucherBot Comprehensive Test Suite

This directory contains comprehensive tests designed to challenge and evaluate the VoucherBot chatbot system. The tests focus on identifying regex aggressiveness, testing the LLM fallback system, and evaluating overall chatbot dynamism.

## 🎯 Test Overview

### Test Categories

1. **Regex Aggressiveness Tests** (`test_regex_aggressiveness.py`)
   - Tests for overly aggressive regex patterns
   - Identifies false positives in intent classification
   - Evaluates parameter extraction precision
   - Tests edge cases and boundary conditions

2. **LLM Fallback System Tests** (`test_llm_fallback_system.py`)
   - Tests LLM fallback system effectiveness
   - Evaluates multilingual support
   - Tests error handling and recovery
   - Evaluates context awareness

3. **Chatbot Dynamism Tests** (`test_chatbot_dynamism.py`)
   - Tests conversation flow adaptation
   - Evaluates context memory and continuity
   - Tests adaptive response to user styles
   - Evaluates performance under stress

## 🚀 Quick Start

### Running All Tests

```bash
# Run all comprehensive tests
python tests/run_comprehensive_tests.py

# Run with verbose output
python tests/run_comprehensive_tests.py --verbose

# Run specific test suite
python tests/run_comprehensive_tests.py --test-suite regex
python tests/run_comprehensive_tests.py --test-suite llm
python tests/run_comprehensive_tests.py --test-suite dynamism
```

### Running Individual Test Files

```bash
# Run regex aggressiveness tests
python -m pytest tests/test_regex_aggressiveness.py -v

# Run LLM fallback tests
python -m pytest tests/test_llm_fallback_system.py -v

# Run dynamism tests
python -m pytest tests/test_chatbot_dynamism.py -v
```

## 📊 Test Results and Reports

### Automated Reporting

The comprehensive test runner generates detailed reports including:

- **Overall Statistics**: Total tests, failures, success rates
- **Suite-by-Suite Breakdown**: Performance by test category
- **Key Findings**: Specific issues and recommendations
- **JSON Report**: Detailed machine-readable results

### Sample Report Output

```
🚀 VoucherBot Comprehensive Test Suite
================================================================================

🔍 Regex Aggressiveness Tests
------------------------------------------------------------
Tests Run: 45
Failures: 2
Errors: 0
Success Rate: 95.6%
✅ All tests passed

📊 COMPREHENSIVE TEST REPORT
================================================================================
📈 OVERALL STATISTICS
  Total Test Duration: 12.34 seconds
  Total Tests Run: 127
  Total Failures: 3
  Total Errors: 1
  Overall Success Rate: 96.9%

🔍 KEY FINDINGS AND RECOMMENDATIONS
------------------------------------------------------------
✅ REGEX PATTERNS APPEAR WELL-TUNED
   - Low false positive rate detected
   - Patterns are appropriately specific
```

## 🔍 Detailed Test Descriptions

### Regex Aggressiveness Tests

#### `test_informational_vs_search_intent()`
Tests that informational questions like "What is a housing listing?" are not misclassified as search requests.

**Example Test Cases:**
- "What is a housing listing?" → Should NOT be `SEARCH_LISTINGS`
- "Tell me about finding apartments" → Should NOT be `SEARCH_LISTINGS`
- "How does apartment hunting work?" → Should NOT be `SEARCH_LISTINGS`

#### `test_borough_mention_vs_what_if_intent()`
Tests that casual borough mentions don't trigger what-if intent classification.

**Example Test Cases:**
- "I live in Brooklyn" → Should NOT be `WHAT_IF`
- "Brooklyn pizza is the best" → Should NOT be `WHAT_IF`
- "Manhattan has tall buildings" → Should NOT be `WHAT_IF`

#### `test_number_extraction_precision()`
Tests that numbers are not over-extracted from inappropriate contexts.

**Example Test Cases:**
- "I live at 123 Main Street" → Should NOT extract `123` as bedrooms
- "I have 3 kids" → Should NOT extract `3` as bedrooms
- "I earn $50,000 per year" → Should NOT extract as max_rent

### LLM Fallback System Tests

#### `test_complex_ambiguous_queries()`
Tests the LLM's ability to handle complex and ambiguous queries that regex cannot process.

**Example Test Cases:**
- "I'm not sure what I'm looking for but I need somewhere to live"
- "My current situation is complicated and I need housing assistance"
- "The landlord said something about my voucher not being accepted"

#### `test_multilingual_support()`
Tests LLM's ability to handle non-English queries.

**Example Test Cases:**
- "Necesito encontrar un apartamento en Brooklyn" (Spanish)
- "我需要在布鲁克林找房子" (Chinese)
- "আমার ব্রুকলিনে একটি অ্যাপার্টমেন্ট দরকার" (Bengali)

#### `test_error_handling_and_recovery()`
Tests the system's ability to handle various error conditions gracefully.

**Test Scenarios:**
- Invalid JSON responses from LLM
- Malformed response structures
- LLM client exceptions
- Network timeouts

### Chatbot Dynamism Tests

#### `test_conversation_flow_adaptation()`
Tests how the chatbot adapts to different conversation styles and flows.

**Conversation Scenarios:**
- **Direct Task-Oriented**: "I need 2BR in Brooklyn" → "Show listings" → "Email landlord"
- **Exploratory Discovery**: "Need housing help" → "What neighborhoods?" → "Try Brooklyn"
- **Problem-Solving**: "Landlord won't accept voucher" → "What are my rights?" → "Find alternatives"

#### `test_context_memory_and_continuity()`
Tests the chatbot's ability to maintain context across conversation turns.

**Context Scenarios:**
- User mentions criteria, then says "show me listings" → Should remember criteria
- User says "try Brooklyn instead" → Should understand what "instead" refers to
- User asks "is that safe?" → Should know what "that" refers to

#### `test_adaptive_response_to_user_style()`
Tests adaptation to different user communication styles.

**User Styles:**
- **Formal Professional**: "I would like to request assistance..."
- **Casual Conversational**: "hey, need help finding a place"
- **Urgent/Stressed**: "I NEED HELP NOW! My lease expires tomorrow!"
- **Detailed/Specific**: "I need 2BR in Park Slope, under $2800, Section 8..."

## 🛠️ Customizing Tests

### Adding New Test Cases

1. **Regex Tests**: Add test cases to `test_regex_aggressiveness.py`
   ```python
   def test_new_regex_pattern(self):
       test_cases = [
           "your test case here",
           "another test case"
       ]
       for case in test_cases:
           intent = self.router_v2.classify_intent(case)
           self.assertEqual(intent, Intent.EXPECTED_INTENT)
   ```

2. **LLM Tests**: Add test cases to `test_llm_fallback_system.py`
   ```python
   def test_new_llm_scenario(self):
       result = self.router.route("your test message")
       self.assertEqual(result["intent"], "EXPECTED_INTENT")
   ```

3. **Dynamism Tests**: Add test cases to `test_chatbot_dynamism.py`
   ```python
   def test_new_conversation_flow(self):
       # Test multi-turn conversation
       messages = ["message 1", "message 2", "message 3"]
       # Test conversation progression
   ```

### Configuring Test Parameters

Edit the test files to adjust:
- **Success Rate Thresholds**: Modify `self.assertGreater(success_rate, 0.8)`
- **Performance Limits**: Modify `self.assertLess(processing_time, 1.0)`
- **Test Data**: Add more test cases to existing lists

## 📈 Performance Benchmarks

### Expected Performance Metrics

| Test Category | Expected Success Rate | Typical Duration |
|---------------|----------------------|------------------|
| Regex Aggressiveness | > 90% | 2-5 seconds |
| LLM Fallback System | > 85% | 5-10 seconds |
| Chatbot Dynamism | > 80% | 3-8 seconds |

### Performance Indicators

- **High Success Rate (>95%)**: System is well-tuned
- **Medium Success Rate (80-95%)**: Some optimization needed
- **Low Success Rate (<80%)**: Significant issues requiring attention

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're running from the project root
   cd /path/to/Voucher
   python tests/run_comprehensive_tests.py
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **LLM Client Issues**
   - Tests use mock LLM clients by default
   - For real LLM testing, configure actual LLM clients

### Test Failures

1. **Regex Aggressiveness Failures**
   - Review failing test cases
   - Check if regex patterns are too broad
   - Consider making patterns more specific

2. **LLM Fallback Failures**
   - Check LLM client configuration
   - Review error handling logic
   - Verify response parsing

3. **Dynamism Test Failures**
   - Review conversation flow logic
   - Check context management
   - Verify adaptive response mechanisms

## 📚 Additional Resources

- **Main Application**: `app.py` - Main chatbot application
- **Regex Patterns**: `enhanced_semantic_router_v2.py` - Updated regex patterns
- **LLM Fallback**: `llm_fallback_router.py` - LLM fallback implementation
- **Documentation**: `README.md` - Main project documentation

## 🤝 Contributing

To contribute new tests:

1. **Identify Test Gaps**: Look for untested scenarios
2. **Add Test Cases**: Follow existing patterns
3. **Update Documentation**: Update this README
4. **Run Tests**: Ensure all tests pass
5. **Submit Changes**: Create pull request

### Test Development Guidelines

- **Comprehensive Coverage**: Test both positive and negative cases
- **Clear Assertions**: Use descriptive assertion messages
- **Performance Awareness**: Consider test execution time
- **Documentation**: Comment complex test logic
- **Maintainability**: Keep tests simple and focused

---

For questions or issues with the test suite, please refer to the main project documentation or create an issue in the project repository. 