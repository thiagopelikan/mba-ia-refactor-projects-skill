/**
 * Controller do relatório financeiro: monta o shape do contrato
 * (course/revenue/students) a partir da query única com JOIN (RP-09).
 * Receita derivada do banco — nenhum acumulador em memória (RP-06).
 */
const { PAYMENT_STATUS } = require('../models/paymentModel');

function createReportController({ courseModel }) {
    async function getFinancialReport(req, res) {
        const rows = await courseModel.getFinancialReportRows();

        const reportByCourse = new Map();
        for (const row of rows) {
            if (!reportByCourse.has(row.courseId)) {
                reportByCourse.set(row.courseId, { course: row.courseTitle, revenue: 0, students: [] });
            }
            if (row.enrollmentId === null) continue; // curso sem matrículas
            const entry = reportByCourse.get(row.courseId);
            if (row.paymentStatus === PAYMENT_STATUS.PAID) {
                entry.revenue += row.paymentAmount;
            }
            entry.students.push({
                student: row.studentName ?? 'Unknown',
                paid: row.paymentAmount ?? 0,
            });
        }

        res.json([...reportByCourse.values()]);
    }

    return { getFinancialReport };
}

module.exports = { createReportController };
