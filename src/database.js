const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
    constructor() {
        this.dbPath = '/app/data/status.db';
        this.init();
    }

    init() {
        this.db = new sqlite3.Database(this.dbPath);
        this.db.run(`CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lado TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )`);
    }

    async updateStatus(lado, status) {
        return new Promise((resolve, reject) => {
            this.db.run(
                'INSERT INTO status_history (lado, status) VALUES (?, ?)',
                [lado, status],
                (err) => {
                    if (err) reject(err);
                    else resolve(true);
                }
            );
        });
    }

    async getLastStatus(lado) {
        return new Promise((resolve, reject) => {
            this.db.get(
                'SELECT status FROM status_history WHERE lado = ? ORDER BY timestamp DESC LIMIT 1',
                [lado],
                (err, row) => {
                    if (err) reject(err);
                    else resolve(row ? row.status : 'LIBERADO');
                }
            );
        });
    }
}

module.exports = new Database(); 