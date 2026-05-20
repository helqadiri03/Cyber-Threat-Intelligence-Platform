// Cyber Threats — MongoDB schema for cyber_intelligence database
// Apply: mongosh < init.js  (or via setup_databases.sh)

const dbName = "cyber_intelligence";
db = db.getSiblingDB(dbName);

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------
db.createCollection("predictions");
db.createCollection("attacker_profiles");
db.createCollection("anomaly_reports");

// ---------------------------------------------------------------------------
// predictions — AI inference results
// ---------------------------------------------------------------------------
db.predictions.createIndex({ source_ip: 1 }, { name: "idx_predictions_source_ip" });
db.predictions.createIndex({ predicted_attack: 1 }, { name: "idx_predictions_predicted_attack" });
db.predictions.createIndex(
  { source_ip: 1, predicted_attack: 1 },
  { name: "idx_predictions_source_ip_attack" }
);
db.predictions.createIndex({ created_at: -1 }, { name: "idx_predictions_created_at" });

// TTL: auto-delete records older than 90 days (adjust expireAfterSeconds as needed)
db.predictions.createIndex(
  { created_at: 1 },
  { name: "idx_predictions_ttl", expireAfterSeconds: 90 * 24 * 60 * 60 }
);

// ---------------------------------------------------------------------------
// attacker_profiles — aggregated per-IP behavioral summaries
// ---------------------------------------------------------------------------
db.attacker_profiles.createIndex({ source_ip: 1 }, { unique: true, name: "idx_profiles_source_ip" });
db.attacker_profiles.createIndex({ risk_score: -1 }, { name: "idx_profiles_risk_score" });
db.attacker_profiles.createIndex({ last_seen: -1 }, { name: "idx_profiles_last_seen" });

// ---------------------------------------------------------------------------
// anomaly_reports — flagged investigation records
// ---------------------------------------------------------------------------
db.anomaly_reports.createIndex({ status: 1, created_at: -1 }, { name: "idx_anomaly_status_created" });
db.anomaly_reports.createIndex({ source_ip: 1 }, { name: "idx_anomaly_source_ip" });
db.anomaly_reports.createIndex(
  { created_at: 1 },
  { name: "idx_anomaly_ttl", expireAfterSeconds: 180 * 24 * 60 * 60 }
);

print(`MongoDB database '${dbName}' configured.`);
print("Collections: predictions, attacker_profiles, anomaly_reports");
printjson(db.getCollectionNames());
print("predictions indexes:");
printjson(db.predictions.getIndexes().map((i) => i.name));
