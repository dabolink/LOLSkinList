from lcu_driver import Connector

def main():
    connector = Connector()

    @connector.ready
    async def connect(connection):
        await getMissingChampionShards(connection)
        await listChampionInfo(connection)


    async def listChampionInfo(connection):
        ownedSkins, champsNoSkins = await getChampionsWithNoSkins(connection)
        items = await getLootInfo(connection , "SKIN")
        championIDs = await getChampionIDNameMap(connection)

        champSkinsAvailiable = dict()
        for champID in champsNoSkins:
            for item in items:
                if champID == item["parentStoreItemId"]:
                    if champID in champSkinsAvailiable:
                        champSkinsAvailiable[champID].append(item["itemDesc"])
                    else:
                        champSkinsAvailiable[champID] = [item["itemDesc"]]
        print(f'owned ::\n')
        for id, skins in ownedSkins.items():
            if len(skins) == 0:
                continue
            print(f'{len(skins)} {id} {skins}')
        print(f'\navailiable:: {len(champSkinsAvailiable)} {champSkinsAvailiable}\n')
        champsUnavailiable = [championIDs[champID] for champID in champsNoSkins if champID not in champSkinsAvailiable]
        print(f'not availiable:: {len(champsUnavailiable)} {champsUnavailiable}')

    async def getLootInfo(connection, type=""):
        lootItemsReq = await connection.request('get', '/lol-loot/v1/player-loot')
        items = [loot for loot in (await lootItemsReq.json()) if loot["displayCategories"] == type or type == ""]
        return items

    async def getSummonerID(connection):
        #get summoner info
        summoner = await connection.request('get', '/lol-summoner/v1/current-summoner')
        summonerID = (await summoner.json())["summonerId"]
        return summonerID

    async def getChampionIDNameMap(connection):
        summonerID = await getSummonerID(connection)
        #get champion info
        championsReq = await connection.request('get', f'/lol-champions/v1/inventories/{summonerID}/champions')
        champions = await championsReq.json()
        return {champ["id"]: champ['name'] for champ in sorted(champions, key=lambda item: item['name'])}

    async def getMissingChampionShards(connection):
        IDToName = await getChampionIDNameMap(connection)
        nameToID = {v: k for k, v in IDToName.items()}
        loot = await getLootInfo(connection, "CHAMPION")
        championShardCount = {champ: 0 for champ in nameToID.keys()}
        for l in loot:
            if l["itemDesc"] not in championShardCount:
                championShardCount[l["itemDesc"]] = l["count"]
            else:
                championShardCount[l["itemDesc"]] += l["count"]
        print(f'0 Champ Shards :: ', [champ for champ, amount in championShardCount.items() if amount == 0])
        print(f'< 2 Champ Shards :: ', [champ for champ, amount in championShardCount.items() if amount < 2])
    
    async def getChampionsWithNoSkins(connection):
        summonerID = await getSummonerID(connection)

        championIDs = await getChampionIDNameMap(connection)

        #get skin info
        totalOwnedSkins = 0
        totalSkins = 0
        noSkins = []
        championSkinMap = dict()
        for championID in championIDs.keys():
            skinsReq = await connection.request('get', f'/lol-champions/v1/inventories/{summonerID}/champions/{championID}/skins')
            skinsJSON = await skinsReq.json()
            ownedSkins = [owned["name"] for owned in skinsJSON if owned["ownership"]["owned"]]
            totalSkins += len(skinsJSON)

            if len(ownedSkins) <= 1:
                noSkins.append(championID)
                championSkinMap[championID] = []
            else:
                championSkinMap[championID] = ownedSkins[1:]
                totalOwnedSkins += len(ownedSkins[1:])
        for champID in championSkinMap.keys():
            if(len(championSkinMap[champID]) > 0):
                pass
        return championSkinMap, noSkins

    connector.start()

if __name__ == '__main__':
    main()