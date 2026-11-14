"""Reuse the indicator's scoring expressions; do not create new sentiment rules. MPL-2.0."""
import re


def scoring_source(indicator):
    constants=re.findall(r'(?m)^(?:TREND|RSI|VOL|HTF)_FILTER_(?:BONUS|PENALTY) = .+$',indicator)
    if len(constants)!=8:raise ValueError('indicator_quality_constants_changed')
    helpers=[]
    for begin,end in (('clampFloat(', 'profileBias('),('profileBias(', 'profileStopAtr('),('qualityLabel(', 'positionFactor(')):
        start=indicator.index('\n'+begin)+1;finish=indicator.index('\n'+end,start)
        helpers.append(indicator[start:finish].rstrip())
    expressions=[]
    for name in ('baseScore','filterScore','score'):
        matches=re.findall(r'(?m)^    '+name+r' = (.+)$',indicator)
        if len(matches)!=1:raise ValueError('indicator_quality_expression_changed')
        expressions.append('    '+name+' = '+matches[0])
    return ('// Quality formula copied from this paired indicator; score is not a win probability.\n'+
        '\n'.join(constants)+'\n\n'+'\n\n'.join(helpers)+'\n\n'+
        'signalQuality(s, trendOk, rsiOk, volatilityOk, htfOk) =>\n'+
        '\n'.join(expressions)+'\n    score\n')
