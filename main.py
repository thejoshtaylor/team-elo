# Team Elo
# Josh Taylor - 2024

import os
import csv
from itertools import permutations
from sympy.utilities.iterables import multiset_permutations

# Defaults
START_ELO = 1000
MIN_TEAM = 3
MAX_TEAM = 13

# Read in and parse the JSON file
def get_data():
    players = []
    if not os.path.exists('players.csv'):
        with open('players.csv', 'w') as f:
            pass
        return players

    with open('players.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                players.append({'name': row[0], 'elo': int(row[1])})
            else:
                break
    return players

# Write the data to the JSON file
def write_data(players):
    print(f"Writing {len(players)} players")
    with open('players.csv', 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows([(player['name'], player['elo']) for player in players])

def title():
    print()
    print(r"""
$$$$$$$$\                                      $$$$$$$$\ $$\           
\__$$  __|                                     $$  _____|$$ |          
   $$ | $$$$$$\   $$$$$$\  $$$$$$\$$$$\        $$ |      $$ | $$$$$$\  
   $$ |$$  __$$\  \____$$\ $$  _$$  _$$\       $$$$$\    $$ |$$  __$$\ 
   $$ |$$$$$$$$ | $$$$$$$ |$$ / $$ / $$ |      $$  __|   $$ |$$ /  $$ |
   $$ |$$   ____|$$  __$$ |$$ | $$ | $$ |      $$ |      $$ |$$ |  $$ |
   $$ |\$$$$$$$\ \$$$$$$$ |$$ | $$ | $$ |      $$$$$$$$\ $$ |\$$$$$$  |
   \__| \_______| \_______|\__| \__| \__|      \________|\__| \______/ 
                                                                       
""")
    print("Josh Taylor - 2024")
    print()

def menu():
    print('[v] View Players')
    print('[n] New Player')
    print('[r] Remove Player')
    print('[u] Update Player')
    print('[g] Generate Teams')
    print('[q] Quit')
    print()

    res = input('> ').lower()
    while res not in ['v', 'n', 'r', 'u', 'g', 'q']:
        print('Invalid choice')
        res = input('> ').lower()

    return res

# Generate the team sizes
def generateTeamSizes(playerCount, MIN_SIZE=MIN_TEAM, MAX_SIZE=MAX_TEAM):
    # TODO allow for a team size that doesn't match, but where there's plentiful players
    options = []

    for i in range(MIN_SIZE, MAX_SIZE + 1):
        numTeams = playerCount // i
        if numTeams * i == playerCount:
            if numTeams % 2 == 0:
                options.append([(i, i)] * (numTeams // 2))

    return options

# Generate the team options
def generateOptions(players, team_sizes=[(5, 5)]):
    options = []

    # Count how many teams we want to make
    teamCount = sum([len(t) for t in team_sizes])

    print(f"Generating {teamCount} teams")

    indexes = []
    for i, (num1, num2) in enumerate(team_sizes):
        indexes.extend([i * 2] * num1)
        indexes.extend([i * 2 + 1] * num2)

    # TODO allow for a team size that doesn't match, but where there's plentiful players
    if len(players) != len(indexes):
        raise ValueError(f"Number of players ({len(players)}) must match the sum of team sizes ({len(indexes)})")
    
    print(indexes)
    perms = list(multiset_permutations(indexes))
    print(f"Generating {len(perms)} permutations")
    
    # Get all orders of indexes
    for ind, p in enumerate(perms):
        per = [(int(a) - int('0')) for a in p]
        print(f" Permutation {ind+1}/{len(perms)}", end='\r')
        teams = []
        for i in range(teamCount):
            teams.append([])
        # build the different teams
        for i, index in enumerate(per):
            teams[index].append(players[i])
        # build a dictionary with pre-calculated elos
        teamsDict = []
        for i, team in enumerate(teams):
            entry = {"team_number": i + 1, "players": team, "elo": sum([player['elo'] for player in team])}
            teamsDict.append(entry)

        options.append(teamsDict)

    # sort by max elo difference
    # TODO make this so it doesn't require even teams (king of the court)
    l = lambda x: sum([abs(x[i]['elo'] - x[i+1]['elo']) for i in range(0, len(x), 2)])

    options.sort(key=l)

    print()
    return options

def getUniquenessOfTeams(team1, team2):
    return len(set([player['name'] for player in team1+team2])) - len(team1)

def getUniquenessOfOptions(option1, option2):
    # get lists of teams
    teams1 = [team['players'] for team in option1]
    teams2 = [team['players'] for team in option2]

    if len(teams1) != len(teams2):
        return len(teams1) + len(teams2)

    # generate all combinations of comparisons
    teams = list(range(1, len(teams1) + 1))
    uniquenesses = []
    for p in permutations(teams):
        uniqueness = 0
        for i in range(len(teams)):
            uniqueness += getUniquenessOfTeams(teams1[i], teams2[p[i]-1])
        uniquenesses.append(uniqueness)

    return int(min(uniquenesses) / 2)


# Main function
def main():
    title()
    players = get_data()
    print(f"Read in {len(players)} players")
    print()

    while True:
        choice = menu()
        if choice == 'v':
            print()
            for player in players:
                print(f"{player['name']} ({player['elo']})")
            print()
        elif choice == 'n':
            name = input('Name: ')
            players.append({'name': name, 'elo': START_ELO})
            print(f"Added {name} with an ELO of {START_ELO}")
            print()
        elif choice == 'r':
            name = input('Name: ')
            for player in players:
                if player['name'] == name:
                    players.remove(player)
                    print(f"Removed {name}")
                    break
            print()
        elif choice == 'u':
            name = input('Name: ')
            for player in players:
                if player['name'] == name:
                    new_elo = int(input('New ELO: '))
                    player['elo'] = new_elo
                    print(f"Updated {name} to {new_elo}")
                    break
            print()
        elif choice == 'g':
            print()
            print(generateTeamSizes(len(players)))
            print()

            options = []

            for i, team_sizes in enumerate(generateTeamSizes(len(players))):
                options.extend(generateOptions(players, team_sizes))
            print(f"Generated {len(options)} options")
            print()

            options.sort(key=lambda x: sum([abs(x[i]['elo'] - x[i+1]['elo']) for i in range(0, len(x), 2)]))

            currentOption = options[0]
            # print elo differences
            for i, option in enumerate(options):
                x = 0
                print(f"[{i+1:3d}]", end=' ')
                for i in range(0, len(option), 2):
                    print(f"({option[i]['elo']} - {option[i + 1]['elo']})", end=' + ')
                    x += abs(option[i]['elo'] - option[i + 1]['elo'])
                print(f'\b\b= {x}', end='')
                print(f" ({getUniquenessOfOptions(currentOption, option)})")

            print()
        elif choice == 'q':
            write_data(players)
            break

if __name__ == '__main__':
    main()