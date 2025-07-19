# Human Handoff Detection System

This module provides intelligent detection of situations where a VoucherBot user should be connected with a human caseworker or housing specialist.

## Features

### 1. User-Driven Triggers
Detects when users explicitly request human assistance:
- Asking to talk to a caseworker
- Expressing confusion
- Requesting human help
- Asking for contact information

### 2. Case-Based Triggers
Detects known escalation scenarios:
- Housing discrimination
- Voucher refusal
- Legal questions
- Rights violations

### 3. Smart Contact Routing
- Maps users to appropriate contacts based on:
  - Voucher type (CityFHEPS, Section 8, HASA)
  - Borough
  - Issue type

## Usage

### Basic Usage
```python
from escalation.handoff_detector import HandoffDetector

# Initialize detector
detector = HandoffDetector()

# Check a message
needs_handoff, reason, contact_info = detector.detect_handoff(
    message="Can I talk to a caseworker?",
    context={"voucher_type": "CityFHEPS"}
)

if needs_handoff:
    # Format response with contact info
    response = detector.format_handoff_message(reason, contact_info)
```

### Integration Example
See `example_integration.py` for a complete example of integrating handoff detection into a chat flow.

## Testing

The system includes comprehensive tests covering:
1. User request detection
2. Case-based trigger detection
3. Contact info lookup
4. Message formatting
5. Integration with search functionality

Run tests with:
```bash
pytest tests/test_handoff_detector.py
```

## Contact Directory

The system includes a comprehensive contact directory (`contact_directory.py`) with:
- Program-specific contact information
- Borough-specific resources
- Default fallback contacts

## Response Format

Handoff responses include:
- Warm, supportive message
- Relevant contact information
- Additional resources when applicable
- Clear next steps

Example response:
```python
{
    "response": "I understand you'd like to speak with a human caseworker...",
    "metadata": {
        "requires_human_handoff": True,
        "handoff_type": "caseworker"
    }
}
```

## Adding New Triggers

To add new handoff triggers:
1. Add patterns to `user_request_patterns` or `case_based_patterns` in `HandoffDetector`
2. Add corresponding test cases in `test_handoff_detector.py`
3. Update contact information if needed in `contact_directory.py`

## Best Practices

1. **Early Detection**: Check for handoff needs before other processing
2. **Clear Communication**: Always provide clear next steps
3. **Contact Accuracy**: Keep contact information up to date
4. **Supportive Tone**: Maintain a helpful, understanding tone
5. **Context Awareness**: Use available context to provide relevant contacts 