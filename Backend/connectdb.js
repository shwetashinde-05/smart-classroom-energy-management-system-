//final Backend code 
const express = require("express");
const mysql = require("mysql2");
const cors = require("cors");
const path = require("path");
const http = require("http");

const app = express();
app.use(express.json());
app.use(cors());

// ✅ Serve static frontend
app.use(express.static(path.join(__dirname, "../Frontend")));

// 🔗 MySQL Connection
const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "#aishu123",  // your password
    database: "classroom_db_mpiv"
});

db.connect(err => {
    if (err) {
        console.log("DB Error:", err);
    } else {
        console.log("✅ MySQL Connected");
    }
});

// ============================================================
// ✅ ORIGINAL ROUTES — DO NOT MODIFY
// ============================================================

app.post("/status", (req, res) => {

    const { classroom, status } = req.body;

    console.log("📥 Received:", req.body);

    const query = `
        INSERT INTO classroom (clsRoom, status, timestamp)
        VALUES (?, ?, NOW())
    `;

    db.query(query, [classroom, status], (err) => {

        if (err) {
            console.log("DB Error:", err);
            return res.send("❌ DB Error");
        }

        res.send("✅ Data saved");
    });

});

// 📤 Send data to ESP32 / frontend
app.get("/latest", (req, res) => {
    db.query(
        "SELECT status FROM classroom ORDER BY id DESC LIMIT 1",
        (err, result) => {
            if (err || result.length === 0) {
                return res.json({ status: "Unoccupied" });
            }
            res.json(result[0]);
        }
    );
});

// ============================================================
// ✅ NEW ROUTES ADDED FOR FRONTEND — DO NOT REMOVE ABOVE
// ============================================================

// 📊 Analytics: last 20 records with timestamps
app.get("/analytics", (req, res) => {
    db.query(
        `SELECT status, timestamp 
         FROM classroom 
         ORDER BY id DESC 
         LIMIT 20`,
        (err, result) => {
            if (err) return res.json([]);
            res.json(result.reverse());
        }
    );
});

// 🧾 Activity Log: last 10 events with classroom info
app.get("/logs", (req, res) => {
    db.query(
        `SELECT clsRoom, status, timestamp 
         FROM classroom 
         ORDER BY id DESC 
         LIMIT 10`,
        (err, result) => {
            if (err) return res.json([]);
            res.json(result);
        }
    );
});

// ⚡ Energy stats: occupied vs unoccupied minutes today
app.get("/energy", (req, res) => {
    db.query(
        `SELECT status, COUNT(*) as count 
         FROM classroom 
         WHERE DATE(timestamp) = CURDATE()
         GROUP BY status`,
        (err, result) => {
            if (err) return res.json({ occupied: 0, unoccupied: 0 });

            let occupied = 0, unoccupied = 0;
            result.forEach(row => {
                if (row.status === "Occupied") occupied = row.count;
                else unoccupied = row.count;
            });

            // Each record ≈ 5 seconds interval
            // Energy saved = unoccupied minutes × 0.1 kWh/hr (example rate)
            const unoccupiedMinutes = (unoccupied * 5) / 60;
            const savedKwh = (unoccupiedMinutes / 60) * 0.5; // 500W device

            res.json({
                occupied,
                unoccupied,
                occupiedMinutes: Math.round((occupied * 5) / 60),
                unoccupiedMinutes: Math.round(unoccupiedMinutes),
                savedKwh: savedKwh.toFixed(2)
            });
        }
    );
});

// 🎥 Webcam stream proxy from Python Flask (port 5000)
// Python must run flask_stream.py separately
app.get("/video", (req, res) => {
    res.setHeader("Content-Type", "text/html");
    res.send(`
        <html><body style="margin:0;background:#000;">
        <img src="http://localhost:5000/video_feed" 
             style="width:100%;height:100%;object-fit:cover;" 
             onerror="this.src='';this.alt='Stream unavailable'"/>
        </body></html>
    `);
});

app.listen(3000, "0.0.0.0", () => {
    console.log("🚀 Server running on port 3000");
});