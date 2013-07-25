var steam = require("steam"),
    util = require("util"),
    fs = require("fs"),
    dota2 = require("../../node-dota2/index"),
    bot = new steam.SteamClient(),
    Dota2 = new dota2.Dota2Client(bot, true),
    MongoClient = require("mongodb").MongoClient;

global.config = require("./config");

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
                MongoClient.connect('mongodb://127.0.0.1:27017/webdota', function(err, db) {
                    if(err) throw err;

                    var jobCollection = db.collection('jobs'),
                        jobCursor = jobCollection.find();

                    jobCursor.each(function (err, doc){
                        if(err) throw err;

                        // If the item is null then the cursor is exhausted/empty and closed
                        if(doc === null) {
                            // Show that the cursor is closed
                            jobCursor.toArray(function(err, items) {
                                // Let's close the db
                                db.close();
                            });
                        }
                        else {
                            if (doc.attempts > config.MAX_ATTEMPTS) {
                                jobCollection.remove({"_id": doc._id}, function(err){ console.log(err); });
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
                                jobCollection.update({"id": doc.id}, doc, function(err){ console.log(err); });
                            }
                        }
                    });
                });
            // }, 5000);
            }, 60000);
        });

        Dota2.on("profileData", function (accountId, profileData) {
            MongoClient.connect('mongodb://127.0.0.1:27017/webdota', function(err, db) {
                if(err) throw err;

                var profileCollection = db.collection('profiles'),
                    jobCollection = db.collection('jobs');

                if (profileData.status) {
                    util.log("Amg a status: "+ profileData.status);
                }
                profileCollection.update({"id": accountId}, {
                    "data": profileData,
                    "id": accountId,
                    "_last_updated": (Date.now() / 1000)
                }, {upsert:true}, function(err){ console.log(err); });
                jobCollection.remove({"type": "account", "id": accountId}, function(err){ console.log(err); });

                db.close();
            });
        });

        Dota2.on("matchData", function (matchId, matchData) {
            MongoClient.connect('mongodb://127.0.0.1:27017/webdota', function(err, db) {
                if(err) throw err;

                var matchCollection = db.collection('matches'),
                    jobCollection = db.collection('jobs');

                if (matchData.status) {
                    util.log("Amg a status: "+ profileData.status);
                }
                matchCollection.update({"id": matchId}, {
                    "data": matchData,
                    "id": matchId,
                    "_last_updated": (Date.now() / 1000)
                }, {upsert:true}, function(err){ console.log(err); });
                jobCollection.remove({"type": "match", "id": matchId}, function(err){ console.log(err); });

                db.close();
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