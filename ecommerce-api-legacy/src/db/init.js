/**
 * DDL + seed (fora dos controllers). Foreign keys com ON DELETE CASCADE
 * protegem a integridade referencial (RP-07); o seed nunca grava senha em
 * claro (RP-01/RP-04) — a senha vem do ambiente ou é gerada aleatoriamente.
 */
const crypto = require('crypto');

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };
const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0 },
    { title: 'Docker', price: 497.0 },
];
const SEED_ENROLLMENT = { userId: 1, courseId: 1 };
const SEED_PAYMENT = { enrollmentId: 1, amount: 997.0, status: 'PAID' };

const RANDOM_PASSWORD_BYTES = 24;

async function initDatabase(db, { passwordService, seedUserPassword, logger }) {
    await db.run('PRAGMA foreign_keys = ON');

    await db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`);
    await db.run(`CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )`);
    await db.run(`CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE
    )`);
    await db.run(`CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`);
    await db.run(`CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`);

    const existingUsers = await db.get('SELECT COUNT(*) AS total FROM users');
    if (existingUsers.total > 0) {
        logger.info('db.init', { seeded: false, reason: 'banco já populado' });
        return;
    }

    const plainPassword = seedUserPassword || crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('base64url');
    const passwordHash = await passwordService.hash(plainPassword);

    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        SEED_USER.name,
        SEED_USER.email,
        passwordHash,
    ]);
    for (const course of SEED_COURSES) {
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', [course.title, course.price]);
    }
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        SEED_ENROLLMENT.userId,
        SEED_ENROLLMENT.courseId,
    ]);
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
        SEED_PAYMENT.enrollmentId,
        SEED_PAYMENT.amount,
        SEED_PAYMENT.status,
    ]);

    logger.info('db.init', { seeded: true, users: 1, courses: SEED_COURSES.length });
}

module.exports = { initDatabase };
