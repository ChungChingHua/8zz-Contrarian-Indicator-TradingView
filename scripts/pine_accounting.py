"""Apply explicit, symmetric win/loss/tie accounting; leave event judgments intact. MPL-2.0."""
def apply_accounting(text):
    if '// AUDITED ACCOUNTING v1' in text:return text
    text=text.replace('if passFilters\n', 'if passFilters and d != 0\n')
    text=text.replace('var int winsA = 0','// AUDITED ACCOUNTING v1: chart bars; A has one independent, non-overlapping position.\nvar int entryBarA = na\nvar float entryPriceA = na\nvar int entryDirA = 0\nvar int tiesA = 0\nvar int tiesB = 0\nvar int winsA = 0')
    start=text.index('if totalFlips > 0 and currentDir != 0 and bar_index - flipBar == holdBars')
    end=text.index('\nif array.size(evt_time)',start)
    text=text[:start]+'''if not na(entryBarA) and bar_index - entryBarA == holdBars
    pnlPctA = entryDirA * (close / entryPriceA - 1) * 100
    pnlSumA += pnlPctA
    if pnlPctA > 0
        winsA += 1
    else if pnlPctA < 0
        lossesA += 1
    else
        tiesA += 1
    entryBarA := na
'''+text[end:]
    text=text.replace('''                        else
                            lossesB += 1
                            array.push(recentB, 0)''','''                        else if pnlPctB < 0
                            lossesB += 1
                            array.push(recentB, 0)
                        else
                            tiesB += 1
                            array.push(recentB, 0)''')
    text=text.replace('''                    currentDir := d
                    posCount := 1''','''                    if na(entryBarA)
                        entryBarA := bar_index
                        entryPriceA := close
                        entryDirA := d
                    currentDir := d
                    posCount := 1''')
    text=text.replace('winsA + lossesA','winsA + lossesA + tiesA').replace('winsB + lossesB','winsB + lossesB + tiesB')
    text=text.replace('str.tostring(lossesA) + "L"','str.tostring(lossesA) + "L/" + str.tostring(tiesA) + "T"').replace('str.tostring(lossesB) + "L"','str.tostring(lossesB) + "L/" + str.tostring(tiesB) + "T"')
    return text
