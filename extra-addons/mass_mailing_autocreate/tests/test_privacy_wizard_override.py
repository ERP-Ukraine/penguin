from odoo.addons.privacy_lookup.tests.test_privacy_wizard import TestPrivacyWizard


def test_wizard(self):
    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    # res.partner now autocreate mailing.contact with same name and email
    self.assertEqual(len(wizard.line_ids), 2)
    self.assertEqual(wizard.line_ids[0].res_id, self.partner.id)
    self.assertEqual(wizard.line_ids[0].res_model, self.partner._name)

    self.assertEqual(wizard.line_ids[1].res_id, self.partner.mailing_contact_ids.id)
    self.assertEqual(
        wizard.line_ids[1].res_model, self.partner.mailing_contact_ids._name
    )
    # ERP end

    self.assertFalse(wizard.log_id)

    # Archive
    # ERP start
    wizard.line_ids[0].is_active = False
    wizard.line_ids[0]._onchange_is_active()
    # ERP end

    self.assertFalse(self.partner.active)
    self.assertEqual(
        wizard.execution_details, 'Archived Contact #%s' % (self.partner.id)
    )
    self.assertTrue(wizard.log_id)
    self.assertEqual(wizard.log_id.anonymized_name, 'R***** T**')
    self.assertEqual(wizard.log_id.anonymized_email, 'r*****.t**@gmail.com')
    self.assertEqual(
        wizard.log_id.execution_details, 'Archived Contact #%s' % (self.partner.id)
    )
    # ERP start
    self.assertEqual(
        wizard.log_id.records_description,
        'Contact (1): #%s\nMailing Contact (1): #%s'
        % (self.partner.id, self.partner.mailing_contact_ids.id),
    )
    # ERP end

    # Delete
    # ERP start
    wizard.line_ids[0].action_unlink()
    # ERP end
    self.assertEqual(
        wizard.execution_details, 'Deleted Contact #%s' % (self.partner.id)
    )
    self.assertEqual(
        wizard.log_id.execution_details, 'Deleted Contact #%s' % (self.partner.id)
    )


def test_wizard_multi_company(self):
    # Check that the record is spotted, even if not available on the Reference field
    self.env['ir.rule'].create(
        {
            'name': 'Multi-Company Rule',
            'model_id': self.env.ref('base.model_res_partner').id,
            'domain_force': "['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]",
        }
    )
    company_2 = self.env['res.company'].create({'name': 'Company 2'})
    other_partner = self.env['res.partner'].create(
        {
            'name': 'Rintin Tin',
            'email': 'rintin.tin@gmail.com',
            'company_id': company_2.id,
        }
    )
    self.assertNotEqual(self.partner.company_id, other_partner.company_id)

    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .with_user(self.env.ref('base.user_admin'))
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    self.assertEqual(len(wizard.line_ids), 4)
    # ERP end
    partner_line = wizard.line_ids.filtered(lambda l: l.resource_ref == self.partner)
    self.assertTrue(partner_line)
    # ERP start
    self.assertEqual(
        (
            wizard.line_ids.filtered(lambda line: line.res_model != 'mailing.contact')
            - partner_line
        ).resource_ref,
        None,
    )
    # ERP end


def test_wizard_direct_reference(self):
    bank = self.env['res.bank'].create(
        {'name': 'ING', 'bic': 'BBRUBEBB', 'email': 'rintin.tin@gmail.com'}
    )

    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    self.assertEqual(len(wizard.line_ids), 3)
    # ERP end
    self.assertEqual(wizard.line_ids[0].res_id, self.partner.id)
    self.assertEqual(wizard.line_ids[0].res_model, self.partner._name)

    self.assertEqual(wizard.line_ids[1].res_id, bank.id)
    self.assertEqual(wizard.line_ids[1].res_model, bank._name)


def test_wizard_indirect_reference(self):
    self.env.company.partner_id = self.partner

    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    self.assertEqual(len(wizard.line_ids), 3)
    # ERP end
    self.assertEqual(wizard.line_ids[0].res_id, self.partner.id)
    self.assertEqual(wizard.line_ids[0].res_model, self.partner._name)

    self.assertEqual(wizard.line_ids[1].res_id, self.env.company.id)
    self.assertEqual(wizard.line_ids[1].res_model, self.env.company._name)


def test_wizard_indirect_reference_cascade(self):
    # Don't retrieve ondelete cascade records
    self.env['res.partner.bank'].create(
        {
            'acc_number': '0123-%s' % self.partner.id,
            'partner_id': self.partner.id,
            'company_id': self.env.company.id,
        }
    )

    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    self.assertEqual(len(wizard.line_ids), 2)
    # ERP end
    self.assertEqual(wizard.line_ids[0].res_id, self.partner.id)
    self.assertEqual(wizard.line_ids[0].res_model, self.partner._name)


def test_wizard_unique_log(self):
    # Check that the log remains unique
    self.env['res.partner'].create(
        {'name': 'Rintin Tin', 'email': 'rintin.tin@gmail.com'}
    )

    wizard = (
        self.env['privacy.lookup.wizard']
        .with_context(
            default_email=self.partner.email,
            default_name=self.partner.name,
        )
        .create({})
    )

    # Lookup
    wizard.action_lookup()
    # ERP start
    self.assertEqual(len(wizard.line_ids), 4)
    # ERP end

    wizard.line_ids[0].is_active = False
    wizard.line_ids[0]._onchange_is_active()
    wizard.execution_details
    self.assertEqual(
        1,
        self.env['privacy.log'].search_count(
            [('anonymized_email', '=', 'r*****.t**@gmail.com')]
        ),
    )

    wizard.line_ids[1].is_active = False
    wizard.line_ids[1]._onchange_is_active()
    wizard.execution_details
    self.assertEqual(
        1,
        self.env['privacy.log'].search_count(
            [('anonymized_email', '=', 'r*****.t**@gmail.com')]
        ),
    )


TestPrivacyWizard.test_wizard = test_wizard
TestPrivacyWizard.test_wizard_multi_company = test_wizard_multi_company
TestPrivacyWizard.test_wizard_direct_reference = test_wizard_direct_reference
TestPrivacyWizard.test_wizard_indirect_reference = test_wizard_indirect_reference
TestPrivacyWizard.test_wizard_indirect_reference_cascade = (
    test_wizard_indirect_reference_cascade
)
TestPrivacyWizard.test_wizard_unique_log = test_wizard_unique_log
