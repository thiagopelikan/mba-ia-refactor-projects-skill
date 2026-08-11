/**
 * Model de cursos. Inclui a query consolidada do relatório financeiro (RP-09):
 * um único JOIN no lugar do padrão N+1 com contadores manuais.
 */
class CourseModel {
    constructor(db) {
        this.db = db;
    }

    findActiveById(courseId) {
        return this.db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [courseId]);
    }

    getFinancialReportRows() {
        return this.db.all(`
            SELECT c.id     AS courseId,
                   c.title  AS courseTitle,
                   e.id     AS enrollmentId,
                   u.name   AS studentName,
                   p.amount AS paymentAmount,
                   p.status AS paymentStatus
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `);
    }
}

module.exports = { CourseModel };
