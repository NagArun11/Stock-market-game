from .companies import Companies 
import random

def getCardStack():
    Cards = []
    id = 0
    for company in Companies:
        for i in range(5, company['maxCardVal']+1, 5):
            Cards.append({
                'type': 'NORMAL',
                'companyId': company['id'],
                'netChange': i,
                'id': id
            })
            id += 1
            Cards.append({
                'type': 'NORMAL',
                'companyId': company['id'],
                'netChange': i,
                'id': id
            })
            id += 1
        for i in range(-5, -company['maxCardVal']-1, -5):
            Cards.append({
                'type': 'NORMAL',
                'companyId': company['id'],
                'netChange': i,
                'id': id
            })
            id += 1
            Cards.append({
                'type': 'NORMAL',
                'companyId': company['id'],
                'netChange': i,
                'id': id
            })
            id += 1
    CrystalCards = [
        {'type': 'CRYSTAL', 'crystalType': 'FRAUD', 'id': id},
        {'type': 'CRYSTAL', 'crystalType': 'DIVIDEND', 'id': id+1},
        {'type': 'CRYSTAL', 'crystalType': 'BONUS_SHARE', 'id': id+2},
        {'type': 'CRYSTAL', 'crystalType': 'RIGHT_ISSUE', 'id': id+3},
        {'type': 'CRYSTAL', 'crystalType': 'LOAN_ON_STOCK', 'id': id+4},
        {'type': 'CRYSTAL', 'crystalType': 'FRAUD', 'id': id+5},
        {'type': 'CRYSTAL', 'crystalType': 'DIVIDEND', 'id': id+6},
        {'type': 'CRYSTAL', 'crystalType': 'BONUS_SHARE', 'id': id+7},
        {'type': 'CRYSTAL', 'crystalType': 'RIGHT_ISSUE', 'id': id+8},
        {'type': 'CRYSTAL', 'crystalType': 'LOAN_ON_STOCK', 'id': id+9},
    ]
    for card in CrystalCards:
        Cards.append(card)
    id+=10
    circuitDenomination = [5, 10, 20]
    for denom in circuitDenomination:
        Cards.append({
            'type': 'CIRCUIT',
            'circuitType': 'UP',
            'denomination': denom,
            'id': id
        })
        id += 1
        Cards.append({
            'type': 'CIRCUIT',
            'circuitType': 'LOW',
            'denomination': denom,
            'id': id
        })
        id += 1
    return Cards


def getShuffledCards(rounds=2,excludeCrystal=False):
    cards = getCardStack()
    if excludeCrystal:
        cards=cards[:116]+cards[126:]
    random.shuffle(cards)
    random.shuffle(cards)
    return cards


