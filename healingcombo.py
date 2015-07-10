import string
import math
import requests
import json

## ------------- Loading Information ----------------

## Retrieve Monster List, Awakening info and Leader Skill info

monsterinfo = requests.get("https://www.padherder.com/api/monsters/")
l_skill = requests.get("https://www.padherder.com/api/leader_skills/")

monsterinfo = monsterinfo.json()
l_skill = l_skill.json()

## -------------- Monster Info Retrieval Functions --------------

## Converts "current_xp"/"xp_curve" into numerical level value

def lvl_get( curr_xp, max_xp ):
    level = ( ( ( float(curr_xp) / float(max_xp) ) ** (1.0 / 2.5) ) * 98 ) + 1
    return int(level)

## Calculates RCV stat using Level obtained from lvl_get() and "rcv_scale" growth rate and additonal boosts from +Eggs/Awakenings
## Also returns the number of Auto-Recover and Bind Recovery Awakenings
## Only used for own monsters, friend leader uses different function

def hprcv_calc( memberInfo, monsInfo, level ):
    ## Counting healing related awakenings
    awakenings = monsInfo["awoken_skills"]
    HP_awkns = 0
    RCV_awkns = 0
    auto_rec= 0
    bind_rec = 0
    counter = 0
    while counter < memberInfo["current_awakening"]:
        if awakenings[counter] == 1:
            HP_awkns += 1
        if awakenings[counter] == 3:
            RCV_awkns += 1
        if awakenings[counter] == 9:
            auto_rec += 1
        if awakenings[counter] == 20:
            bind_rec += 1 
        counter += 1
    ## Calculating HP/Recovery Stat based on Level
    plus_hp = memberInfo["plus_hp"]
    plus_rcv = memberInfo["plus_rcv"]
    max_level = monsInfo["max_level"]
    min_rcv = monsInfo["rcv_min"]
    max_rcv = monsInfo["rcv_max"]
    rcv_scale = monsInfo["rcv_scale"]
    min_hp = monsInfo["hp_min"]
    max_hp = monsInfo["hp_max"]
    hp_scale = monsInfo["hp_scale"]

    if level == max_level:
        rcv = max_rcv
        hp = max_hp
    else:
        rcv = min_rcv + (max_rcv - min_rcv)*( (float(level - 1)/float(max_level - 1))** rcv_scale )
        hp = min_hp + (max_hp - min_hp)*( (float(level - 1)/float(max_level - 1))** hp_scale )

    ## Adding bonus stats from +Eggs and Awakenings
    rcv = int(round(rcv)) + (plus_rcv * 3) + (RCV_awkns * 50)
    hp = int(round(hp)) + (plus_hp * 10) + (HP_awkns * 200)
    recovery_stats = [hp, rcv, auto_rec, bind_rec]
    
    return recovery_stats

## Calculating friend leader stats via ID and info directly from a teamobj
def friend_stats( ID, teamobj ):
    for ele in monsterinfo:
        if ele["id"] == ID:
            monsEntry = ele
            break

    awakenings = monsEntry[ "awoken_skills" ]
    unlocked_awkns = teamobj["friend_awakening"]
    curr_level = teamobj["friend_level"]
    max_lvl = monsEntry["max_level"]
    plus_hp = teamobj["friend_hp"]
    plus_rcv = teamobj["friend_rcv"]
    min_rcv = monsEntry["rcv_min"]
    max_rcv = monsEntry["rcv_max"]
    rcv_scale = monsEntry["rcv_scale"]
    min_hp = monsEntry["hp_min"]
    max_hp = monsEntry["hp_max"]
    hp_scale = monsEntry["hp_scale"]
    HP_awkns = 0
    RCV_awkns = 0
    auto_rec= 0
    bind_rec = 0
    counter = 0
    while counter < unlocked_awkns:
        if awakenings[counter] == 1:
            HP_awkns += 1
        if awakenings[counter] == 3:
            RCV_awkns += 1
        if awakenings[counter] == 9:
            auto_rec += 1
        if awakenings[counter] == 20:
            bind_rec += 1 
        counter += 1
    if curr_level == max_lvl:
        rcv = max_rcv
        hp = max_hp
    else:
        rcv = min_rcv + (max_rcv - min_rcv)*( (float(level - 1)/float(max_level - 1))** rcv_scale )
        hp = min_hp + (max_hp - min_hp)*( (float(level - 1)/float(max_level - 1))** hp_scale )

    ## Adding bonus stats from +Eggs and Awakenings
    rcv = int(round(rcv)) + (plus_rcv * 3) + (RCV_awkns * 50)
    hp = int(round(hp)) + (plus_hp * 10) + (HP_awkns * 200)
    recovery_stats = [hp, rcv, auto_rec, bind_rec]
    
    return recovery_stats
    

## Determining RCV multiplier given by both leaders using input from user
def get_multiplier( stat ):
    multiplier = input("Own leader skill " + stat + " multiplier (1 for no multiplier): ")
    multiplier = float(multiplier) 
    while float(multiplier) <= 0.0:
        multiplier = input("Invalid Leader Multiplier, must be greater than 0: ")
        multiplier = float(multiplier)
    f_multiplier = input("Friend leader skill " + stat + " multiplier (1 for no multiplier): ")
    f_multiplier = float(f_multiplier)
    while float(f_multiplier) <= 0:
        f_multiplier = input("Invalid Leader Multiplier, must be greater than 0: ")
        f_multiplier = float(f_multiplier)
    return multiplier * f_multiplier    
    
## Retrives all relevant information for one team member and places into list

def statget( team_member, teamobj ):
    mons = requests.get("https://www.padherder.com/user-api/monster/" + str(teamobj[team_member]))
    mons = mons.json()
    ID = mons["monster"]
    for ele in monsterinfo:
        if ele["id"] == ID:
            monsEntry = ele
            break
    
    curr = mons["current_xp"]
    max_exp = monsEntry["xp_curve"]
    stats = hprcv_calc( mons, monsEntry, lvl_get(curr,max_exp) )

    return stats

## Checking function if team slot other than the leader is empty

def memberget( slotname , teamobj ):
    empty_teamslot = [0, 0, 0, 0]
    if teamobj[slotname]:
        sub = statget( slotname, teamobj )
    else:
        sub = empty_teamslot
    return sub

## Output passive bonuses obtained through awakenings
def passive_skills( team_statlist ):
    heal_amt = 500 * team_statlist[2]
    bind_rec = 3 * team_statlist[3]
    if heal_amt != 0:
        print "Your Team will Recover " + heal_amt + " HP after every turn."
    if bind_rec != 0:
        print "Your Team will clear up to " + bind_rec + " turns for every row of hearts matched. Assuming the units with the awakenings are not disabled."
    return

## Orb matching power calculation formula: 100%+(n-3)*25%, n=number of connected orbs 
def orbpower( number_matched ):
    value = 1.0 + (number_matched - 3)*1.25
    return round(value, 2)
    
## ------------- Main Program ---------------

print "PAD Combo Healing Calculator v0.01"

urlID = input("Enter PADherder team ID: ")

while type(urlID) is not int:
    urlID = input("Only numerical values are accepted\nEnter only the number that appears at the end of your PADHerder team URL: ")

team_url = "https://www.padherder.com/user-api/team/" + str(urlID)
team = requests.get( team_url )
team = team.json()

hp_mult = get_multiplier( "HP" )
rcv_mult = get_multiplier( "RCV" )

leader = statget("leader", team)
sub1 = memberget("sub1", team)
sub2 = memberget("sub2", team)
sub3 = memberget("sub3", team)
sub4 = memberget("sub4", team)
friend = friend_stats(team["friend_leader"], team)

# Obtaining team total HP and recovery
team_stats = [0,0,0,0]

for x in range(4):
    team_stats[x] = leader[x] + sub1[x] + sub2[x] + sub3[x] + sub4[x] + friend[x]








    
    
