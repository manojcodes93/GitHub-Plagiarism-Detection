from typing import List, Dict

class LLMReasoner:
    def __init__(self):
        self.model = None
        self.model_name = "rule-based"
    
    def batch_judge_files(self, file_pairs):
        """
        Judge multiple file pairs for plagiarism.
        """
        judgments = []
        for pair in file_pairs:
            judgment = self.judge_file_similarity(
                pair['file1'],
                pair['file2'],
                pair.get('similarity', 0.5)
            )
            judgments.append(judgment)
        return judgments
    
    def generate_plagiarism_explanation(self, repo1_name, repo2_name, file_pairs, similarity):
        """Generate explanation for plagiarism detection."""
        return self.generate_repository_report(repo1_name, repo2_name, file_pairs, similarity)

    def judge_file_similarity(
        self,
        file1_path: str,
        file2_path: str,
        similarity_score: float
    ) -> Dict:
        ## Deciding if two files indicate plagiarism based on similarity score
        if similarity_score >= 0.95:
            return {
                "is_plagiarism": True,
                "confidence": 0.95,
                "reason": "Extremely high similarity",
                "explanation": (
                    f"The files {file1_path} and {file2_path} "
                    f"have very high semantic similarity "
                    f"({similarity_score:.2%}), which strongly suggests plagiarism."
                )
            }
        
        if similarity_score >= 0.85:
            return {
                "is_plagiarism": True,
                "confidence": 0.75,
                "reason": "Very high similarity",
                "explanation": (
                    f"High semantic similarity ({similarity_score:.2%}) detected. "
                    f"The logic appears highly similar."
                )
            }
        
        if similarity_score >= 0.75:
            return {
                "is_plagiarism": True,
                "confidence": 0.75,
                "reason": "Moderate-High similarity",
                "explanation": (
                    f"Similarity score ({similarity_score:.2%}) "
                    f"suggests potential plagiarism."
                )
            }
        
        if similarity_score >= 0.65:
            return {
                "is_plagiarism": False,
                "confidence": 0.6,
                "reason": "Low-moderate similarity",
                "explanation": (
                    f"Similarity score ({similarity_score:.2%}) "
                    f"may be due to common patterns."
                )
            }
        
        return {
            "is_plagiarism": False,
            "confidence": 0.85,
            "reason": "Low similarity",
            "explanation": (
                f"Similarity score ({similarity_score:.2%}) "
                f"is within a normal range."
            )
        }
    
    def judge_commit_similarity(
        self,
        commit1_message: str,
        commit2_message: str,
        similarity_score: float
    ) -> Dict:
        ## Decide if two commits indicate plagiarism
        reasons = []
        confidence = 0.5

        if commit1_message.strip() == commit2_message.strip():
            reasons.append("Identical commit messages")
            confidence = 0.8

        if similarity_score >= 0.9:
            reasons.append("Very similar code changes")
            confidence = max(confidence, 0.85)

        is_plagiarism = confidence >= 0.7

        return {
            "is_plagiarism": is_plagiarism,
            "confidence": confidence,
            "reason": ", ".join(reasons) if reasons else "Moderate similarity",
            "explanation": (
                f"Commits show {similarity_score:.2%} similarity. "
                f"Observed patterns: {', '.join(reasons) if reasons else 'None'}."
            )
        }
    
    def generate_repository_report(
        self,
        repo1_name: str,
        repo2_name: str,
        file_results: List[Dict],
        repo_similarity: float
    ) -> str:
        ## Generate enhanced plagiarism report with detailed formatting
        from datetime import datetime
        
        report = []
        report.append("=" * 80)
        report.append("PLAGIARISM ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Analysis metadata
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Repositories section
        report.append("REPOSITORIES")
        report.append("├─ Repo 1: " + repo1_name)
        report.append("└─ Repo 2: " + repo2_name)
        report.append("")
        
        # Overall risk assessment
        risk_level = "🔴 CRITICAL" if repo_similarity >= 0.85 else "🟡 WARNING" if repo_similarity >= 0.75 else "🟢 LOW RISK"
        confidence_score = min(0.95, repo_similarity + 0.05)  # Confidence increases with similarity
        
        report.append("OVERALL RISK ASSESSMENT")
        report.append(f"├─ Repository Similarity: {repo_similarity:.2%} {risk_level}")
        report.append(f"├─ Suspicious Pairs: {len(file_results)}")
        report.append(f"└─ Confidence Level: {confidence_score:.0%}")
        report.append("")
        
        # Top suspicious matches
        if file_results:
            report.append("TOP SUSPICIOUS MATCHES")
            for idx, result in enumerate(file_results[:10], start=1):
                similarity_pct = result['similarity'] * 100
                match_status = "🚨 CRITICAL" if result['similarity'] >= 0.95 else "⚠️  HIGH" if result['similarity'] >= 0.85 else "⚡ MEDIUM"
                
                report.append(f"{idx}. [{result['similarity']:.2%}] {match_status}")
                report.append(f"   File 1: {result['file1']}")
                report.append(f"   File 2: {result['file2']}")
                report.append("")
            
            if len(file_results) > 10:
                report.append(f"... and {len(file_results) - 10} more suspicious file pairs")
                report.append("")
        else:
            report.append("✅ NO SUSPICIOUS FILE PAIRS DETECTED")
            report.append("")
        
        # Verdict
        report.append("=" * 80)
        if repo_similarity >= 0.85:
            verdict = "🛑 LIKELY PLAGIARISM - IMMEDIATE INVESTIGATION RECOMMENDED"
            recommendations = [
                "Review commit history for similarity patterns",
                "Check for shared common dependencies or libraries",
                "Compare code structure and logic flow between files",
                "Investigate potential code reuse or copying"
            ]
        elif repo_similarity >= 0.75:
            verdict = "⚠️  SUSPICIOUS - REQUIRES DETAILED REVIEW"
            recommendations = [
                "Examine the flagged file pairs manually",
                "Check if repositories share legitimate common dependencies",
                "Analyze commit timestamps for timeline correlation",
                "Verify if similarity is due to following same tutorial/pattern"
            ]
        else:
            verdict = "✅ LOW RISK - NO ACTION REQUIRED"
            recommendations = [
                "Repositories show normal code diversity",
                "Similarity levels consistent with independent development",
                "Continue monitoring for future changes"
            ]
        
        report.append(f"VERDICT: {verdict}")
        report.append("")
        
        report.append("RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"  {i}. {rec}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)