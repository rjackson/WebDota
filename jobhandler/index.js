var steam = require("steam"),
    util = require("util"),
    fs = require("fs"),
    Db = require('mongodb').Db,
    Server = require('mongodb').Server,
    dota2 = require("../../node-dota2/index"),
    bot = new steam.SteamClient(),
    Dota2 = new dota2.Dota2Client(bot, true);

global.config = require("./config");

db= new Db('webdota', new Server("localhost", 27017, {auto_reconnect: true}), {w: 0});
db.open(function(){});

/* Steam logic */
var onSteamLogOn = function onSteamLogOn(){
        bot.setPersonaState(steam.EPersonaState.Busy); // to display your bot's status as "Online"
        bot.setPersonaName(config.steam_name); // to change its nickname
        util.log("Logged on.");

        Dota2.launch();
        Dota2.on("ready", function() {
            setInterval(function handleJobQueue(){
            // setTimeout(function handleJobQueue(){
                util.log("Handling jobs");
                db.collection("jobs", function(err, Collection) {
                    Collection.find(function(err, jobs){
                        jobs.each(function (err, doc){
                            if(err) throw err;
                            if (doc === null) return;

                            if (doc.attempts > config.MAX_ATTEMPTS) {
                                Collection.remove({"_id": doc._id}, function(err){ console.log(err); });
                            }
                            else {
                                switch (doc.type) {
                                    case "account":
                                        Dota2.profileRequest(doc.id, true);
                                        break;
                                    case "match":
                                        Dota2.matchDetailsRequest(doc.id);
                                        break;
                                }
                                doc.attempts += 1;
                                Collection.update({"id": doc.id}, doc, function(err){ console.log(err); });
                            }
                        });
                    });
                });
            // }, 5000);
            }, 60000);
        });

        Dota2.on("profileData", function (accountId, profileData) {
            db.collection('profiles', function(err, profileCollection) {
                if(err) throw err;
                db.collection('jobs', function(err, jobCollection){
                    if(err) throw err;
                    if (profileData.status) {
                        util.log("Amg a status: " + profileData.status);
                    }
                    profileCollection.update({"id": accountId}, {
                        "data": profileData,
                        "id": accountId,
                        "_last_updated": (Date.now() / 1000)
                    }, {upsert:true}, function(err){ console.log(err); });
                    jobCollection.remove({"type": "account", "id": accountId}, function(err){ console.log(err); });
                });

                if (profileData.hasPassport) {
                    Dota2.passportDataRequest(accountId);
                }
            });
        });

        Dota2.on("passportData", function(accountId, passportData) {
            db.collection('profiles', function(err, profileCollection) {
                profileCollection.findOne({"id": accountId}, function(err, data){
                    data.passportData = passportData;
                    profileCollection.update({"id": accountId}, data, {upsert:true}, function(err){ console.log(err); });
                });
            });
        });

        Dota2.on("matchData", function (matchId, matchData) {
            db.collection('matches', function(err, matchCollection) {
                if(err) throw err;
                db.collection('jobs', function(err, jobCollection){
                    if(err) throw err;
                    if (matchData.status) {
                        util.log("Amg a status: " + profileData.status);
                    }
                    matchCollection.update({"id": matchId}, {
                        "data": matchData,
                        "id": matchId,
                        "_last_updated": (Date.now() / 1000)
                    }, {upsert:true}, function(err){ console.log(err); });
                    jobCollection.remove({"type": "match", "id": matchId}, function(err){ console.log(err); });

                });
            });
        });

        Dota2.on("unhandled", function(kMsg) {
            util.log("UNHANDLED MESSAGE " + kMsg);
        });
    },
    onSteamSentry = function onSteamSentry(sentry) {
        util.log("Received sentry.");
        require('fs').writeFileSync('sentry', sentry);
    },
    onSteamServers = function onSteamServers(servers) {
        util.log("Received servers.");
        fs.writeFile('servers', JSON.stringify(servers));
    };

bot.logOn({
    "accountName": config.steam_user,
    "password": config.steam_pass,
    "authCode": config.steam_guard_code,
    "shaSentryfile": fs.readFileSync('sentry')
});
bot.on("loggedOn", onSteamLogOn)
    .on('sentry', onSteamSentry)
    .on('servers', onSteamServers);