#!/usr/bin/env python3
"""
Comprehensive Test Runner for VoucherBot

This script runs all comprehensive tests to evaluate:
1. Regex aggressiveness and false positive rates
2. LLM fallback system effectiveness
3. Overall chatbot dynamism and adaptability
4. Performance under various conditions
5. Error handling and recovery

Usage:
    python run_comprehensive_tests.py [--verbose] [--test-suite TEST_SUITE]
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from test_regex_aggressiveness import TestRegexAggressiveness
from test_llm_fallback_system import TestLLMFallbackSystem
from test_chatbot_dynamism import TestChatbotDynamism


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self):
        """Run all comprehensive test suites"""
        
        print("🚀 VoucherBot Comprehensive Test Suite")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.start_time = time.time()
        
        # Test suites to run
        test_suites = [
            {
                "name": "Regex Aggressiveness Tests",
                "description": "Tests to identify overly aggressive regex patterns",
                "test_class": TestRegexAggressiveness,
                "icon": "🔍"
            },
            {
                "name": "LLM Fallback System Tests", 
                "description": "Tests for LLM fallback system effectiveness",
                "test_class": TestLLMFallbackSystem,
                "icon": "🧠"
            },
            {
                "name": "Chatbot Dynamism Tests",
                "description": "Tests for overall chatbot adaptability and dynamism",
                "test_class": TestChatbotDynamism,
                "icon": "🎭"
            }
        ]
        
        # Run each test suite
        for suite_info in test_suites:
            self._run_test_suite(suite_info)
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        self._generate_report()
        
    def _run_test_suite(self, suite_info):
        """Run a single test suite"""
        
        print(f"{suite_info['icon']} {suite_info['name']}")
        print("-" * 60)
        print(f"Description: {suite_info['description']}")
        print()
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_info['test_class'])
        
        # Capture output
        output_buffer = StringIO()
        error_buffer = StringIO()
        
        # Run tests with custom result handler
        with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
            runner = unittest.TextTestRunner(
                stream=output_buffer,
                verbosity=2 if self.verbose else 1,
                buffer=True
            )
            result = runner.run(suite)
        
        # Store results
        self.results[suite_info['name']] = {
            'result': result,
            'output': output_buffer.getvalue(),
            'errors': error_buffer.getvalue(),
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
        }
        
        # Print summary
        suite_result = self.results[suite_info['name']]
        print(f"Tests Run: {suite_result['tests_run']}")
        print(f"Failures: {suite_result['failures']}")
        print(f"Errors: {suite_result['errors']}")
        print(f"Success Rate: {suite_result['success_rate']:.1%}")
        
        if suite_result['failures'] > 0 or suite_result['errors'] > 0:
            print("❌ Some tests failed")
        else:
            print("✅ All tests passed")
        
        print()
        
        # Show detailed output if verbose
        if self.verbose and suite_result['output']:
            print("Detailed Output:")
            print(suite_result['output'])
            print()
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        total_duration = self.end_time - self.start_time
        
        # Overall statistics
        total_tests = sum(r['tests_run'] for r in self.results.values())
        total_failures = sum(r['failures'] for r in self.results.values())
        total_errors = sum(r['errors'] for r in self.results.values())
        overall_success_rate = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0
        
        print(f"📈 OVERALL STATISTICS")
        print(f"  Total Test Duration: {total_duration:.2f} seconds")
        print(f"  Total Tests Run: {total_tests}")
        print(f"  Total Failures: {total_failures}")
        print(f"  Total Errors: {total_errors}")
        print(f"  Overall Success Rate: {overall_success_rate:.1%}")
        print()
        
        # Per-suite breakdown
        print(f"🔍 SUITE-BY-SUITE BREAKDOWN")
        for suite_name, suite_result in self.results.items():
            status = "✅ PASSED" if suite_result['failures'] == 0 and suite_result['errors'] == 0 else "❌ FAILED"
            print(f"  {suite_name}: {status}")
            print(f"    Tests: {suite_result['tests_run']}")
            print(f"    Success Rate: {suite_result['success_rate']:.1%}")
            if suite_result['failures'] > 0:
                print(f"    Failures: {suite_result['failures']}")
            if suite_result['errors'] > 0:
                print(f"    Errors: {suite_result['errors']}")
            print()
        
        # Specific findings and recommendations
        self._generate_findings_and_recommendations()
        
        # Save detailed report to file
        self._save_detailed_report()
        
    def _generate_findings_and_recommendations(self):
        """Generate specific findings and recommendations"""
        
        print(f"🔍 KEY FINDINGS AND RECOMMENDATIONS")
        print("-" * 60)
        
        # Analyze regex aggressiveness results
        regex_results = self.results.get("Regex Aggressiveness Tests")
        if regex_results:
            if regex_results['success_rate'] < 0.8:
                print("⚠️  REGEX AGGRESSIVENESS ISSUES DETECTED")
                print("   - Some regex patterns may be too aggressive")
                print("   - Consider making patterns more specific")
                print("   - Review false positive cases")
            else:
                print("✅ REGEX PATTERNS APPEAR WELL-TUNED")
                print("   - Low false positive rate detected")
                print("   - Patterns are appropriately specific")
            print()
        
        # Analyze LLM fallback results
        llm_results = self.results.get("LLM Fallback System Tests")
        if llm_results:
            if llm_results['success_rate'] < 0.9:
                print("⚠️  LLM FALLBACK SYSTEM NEEDS ATTENTION")
                print("   - Some edge cases not handled properly")
                print("   - Consider improving error handling")
                print("   - Review multilingual support")
            else:
                print("✅ LLM FALLBACK SYSTEM PERFORMING WELL")
                print("   - Good error handling and recovery")
                print("   - Effective multilingual support")
            print()
        
        # Analyze dynamism results
        dynamism_results = self.results.get("Chatbot Dynamism Tests")
        if dynamism_results:
            if dynamism_results['success_rate'] < 0.85:
                print("⚠️  CHATBOT DYNAMISM COULD BE IMPROVED")
                print("   - Context handling may need enhancement")
                print("   - Consider improving conversation flow")
                print("   - Review adaptive response mechanisms")
            else:
                print("✅ CHATBOT SHOWS GOOD DYNAMISM")
                print("   - Effective context management")
                print("   - Good conversation flow adaptation")
            print()
        
        # Overall system health
        total_tests = sum(r['tests_run'] for r in self.results.values())
        total_failures = sum(r['failures'] for r in self.results.values())
        total_errors = sum(r['errors'] for r in self.results.values())
        
        if total_tests > 0:
            overall_success_rate = (total_tests - total_failures - total_errors) / total_tests
            if overall_success_rate >= 0.9:
                print("🎉 OVERALL SYSTEM HEALTH: EXCELLENT")
                print("   - System is performing very well")
                print("   - Minor optimizations may still be beneficial")
            elif overall_success_rate >= 0.8:
                print("👍 OVERALL SYSTEM HEALTH: GOOD")
                print("   - System is performing well")
                print("   - Some areas for improvement identified")
            elif overall_success_rate >= 0.7:
                print("⚠️  OVERALL SYSTEM HEALTH: NEEDS ATTENTION")
                print("   - Several issues need to be addressed")
                print("   - Consider prioritizing fixes")
            else:
                print("🚨 OVERALL SYSTEM HEALTH: CRITICAL")
                print("   - Significant issues detected")
                print("   - Immediate attention required")
        
        print()
        
    def _save_detailed_report(self):
        """Save detailed report to JSON file"""
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': self.end_time - self.start_time,
            'results': {}
        }
        
        # Convert results to serializable format
        for suite_name, suite_result in self.results.items():
            report_data['results'][suite_name] = {
                'tests_run': suite_result['tests_run'],
                'failures': suite_result['failures'],
                'errors': suite_result['errors'],
                'success_rate': suite_result['success_rate'],
                'output': suite_result['output'][:1000] if suite_result['output'] else "",  # Truncate for size
            }
        
        # Save to file
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_filename}")
        print()


def main():
    """Main function to run comprehensive tests"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive VoucherBot tests")
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    parser.add_argument('--test-suite', '-t', 
                       choices=['regex', 'llm', 'dynamism', 'all'],
                       default='all',
                       help='Specific test suite to run')
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = ComprehensiveTestRunner(verbose=args.verbose)
    
    if args.test_suite == 'all':
        runner.run_all_tests()
    else:
        # Run specific test suite
        suite_map = {
            'regex': TestRegexAggressiveness,
            'llm': TestLLMFallbackSystem,
            'dynamism': TestChatbotDynamism
        }
        
        if args.test_suite in suite_map:
            suite_info = {
                'name': f"{args.test_suite.title()} Tests",
                'description': f"Running {args.test_suite} tests only",
                'test_class': suite_map[args.test_suite],
                'icon': '🔍'
            }
            runner._run_test_suite(suite_info)
        else:
            print(f"Unknown test suite: {args.test_suite}")
            sys.exit(1)


if __name__ == "__main__":
    main() 