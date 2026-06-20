#!/usr/bin/env python3
"""
Generate betting recommendations based on Sofascore and CGMBet26 data.
"""

import sys
import json

def generate_recommendations(sofadata, cgmdata=None):
    """Generate structured betting recommendations."""
    
    recommendations = []
    risk_factors = []
    timing_advice = []
    
    # Extract key metrics
    xg_total = sofadata.get('xg_home', 0) + sofadata.get('xg_away', 0)
    shots_total = sofadata.get('shots_home', 0) + sofadata.get('shots_away', 0)
    momentum = sofadata.get('momentum_10min', 0)
    big_chances = sofadata.get('big_chances_home', 0) + sofadata.get('big_chances_away', 0)
    
    # Determine match phase (simplified)
    status = sofadata.get('status', '').lower()
    if 'half' in status or '2nd' in status or 'second' in status:
        match_phase = 'second_half'
    else:
        match_phase = 'first_half'
    
    # Analysis logic
    
    # 1. Over 0.5 Goals recommendation
    if xg_total > 1.0 and shots_total > 8:
        if momentum > 50:
            recommendations.append({
                'priority': 1,
                'market': 'Over 0.5 Goals',
                'selection': 'BACK',
                'confidence': '⭐⭐⭐⭐',
                'rationale': f'High xG ({xg_total:.2f}), {shots_total} shots, strong momentum (+{momentum})'
            })
        else:
            recommendations.append({
                'priority': 2,
                'market': 'Over 0.5 Goals',
                'selection': 'BACK',
                'confidence': '⭐⭐⭐',
                'rationale': f'Good xG ({xg_total:.2f}) but momentum neutral'
            })
    
    # 2. Under 2.5 Goals (if low xG and few chances)
    if xg_total < 1.2 and big_chances < 2:
        recommendations.append({
            'priority': 2,
            'market': 'Under 2.5 Goals',
            'selection': 'BACK',
            'confidence': '⭐⭐⭐⭐',
            'rationale': f'Low xG ({xg_total:.2f}), only {big_chances} big chances'
        })
    
    # 3. Both Teams to Score
    if sofadata.get('xg_home', 0) > 0.4 and sofadata.get('xg_away', 0) > 0.4:
        if shots_total > 10:
            recommendations.append({
                'priority': 3,
                'market': 'Both Teams to Score',
                'selection': 'YES',
                'confidence': '⭐⭐⭐',
                'rationale': 'Both teams creating chances'
            })
    
    # Risk factors
    if big_chances > 0:
        risk_factors.append(f"{big_chances} big chance(s) created but not converted - finishing may be poor")
    
    if abs(momentum) < 20:
        risk_factors.append("Match is balanced with no clear momentum - goal timing unpredictable")
    
    if sofadata.get('shots_on_target_home', 0) + sofadata.get('shots_on_target_away', 0) < 3:
        risk_factors.append("Low shot accuracy - may indicate poor finishing or strong defending")
    
    # Timing advice
    if match_phase == 'second_half':
        timing_advice.append("Second half: Goal probability increases with time - consider late entry if still 0-0 at 70'")
    
    if momentum > 50:
        timing_advice.append("Strong momentum detected - entry recommended within next 5 minutes")
    
    return {
        'recommendations': sorted(recommendations, key=lambda x: x['priority']),
        'risk_factors': risk_factors,
        'timing_advice': timing_advice,
        'summary': f"Based on xG {xg_total:.2f}, {shots_total} shots, momentum {momentum:+d}"
    }

def format_output(data):
    """Format recommendations as markdown."""
    lines = []
    
    lines.append("### 💰 Recommendations")
    lines.append("")
    lines.append("| Priority | Market | Selection | Confidence | Rationale |")
    lines.append("|----------|--------|-----------|------------|-----------|")
    
    for rec in data['recommendations']:
        lines.append(f"| ⭐{rec['priority']} | {rec['market']} | {rec['selection']} | {rec['confidence']} | {rec['rationale']} |")
    
    if not data['recommendations']:
        lines.append("| - | No clear recommendation | - | - | Insufficient signals |")
    
    lines.append("")
    lines.append("### ⏰ Timing Advice")
    for advice in data['timing_advice']:
        lines.append(f"- {advice}")
    
    lines.append("")
    lines.append("### ⚠️ Risk Factors")
    for risk in data['risk_factors']:
        lines.append(f"- {risk}")
    
    return "\n".join(lines)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: generate_recommendation.py <sofadata_json> [cgmdata_json]", file=sys.stderr)
        sys.exit(1)
    
    try:
        sofadata = json.loads(sys.argv[1])
        cgmdata = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
        
        result = generate_recommendations(sofadata, cgmdata)
        
        # Output both JSON and formatted markdown
        output = {
            'json': result,
            'markdown': format_output(result)
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), indent=2)
        sys.exit(1)
