from odoo import models,fields,api

class StudentFee(models.Model):
    _name='student.fee'
    _description='Student Fee'
    student_name=fields.Char(string="student name",required=True)
    course=fields.Selection([('python','Python'),('java','Java'),('c++','C++')],string='Course')
    course_fee=fields.Float(string="Course Fee")
    discount=fields.Float(string="Discount %")
    final_fees=fields.Float(string="Final Fees",compute='_compute_final_fees',store=True)

    @api.onchange('course')
    def _onchange_course(self):
        if self.course=='python':
            self.course_fee=10000
        elif self.course=='java':
            self.course_fee=12000
        elif self.course=='c++':
            self.course_fee=15000
        else:
            self.course_fee=0


    @api.depends('course_fee','discount')
    def _compute_final_fees(self):
        for rec in self:
            rec.final_fees=rec.course_fee-(rec.course_fee*rec.discount/100)

