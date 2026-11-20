/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
using Microsoft.VisualStudio.TestTools.UnitTesting;
using s2industries.ZUGFeRD;
using System.IO;
using System.Text;

namespace s2industries.ZUGFeRD.Test
{
    /// <summary>
    /// Reading UBL must not invent values that are not in the document (maintenance fork).
    /// </summary>
    [TestClass]
    public class UblReadingTests : TestBase
    {
        private const string TaxTotal = "   <cac:TaxTotal>";

        private const string AllowanceWithoutCodeAndBase =
            "   <cac:AllowanceCharge>\n" +
            "      <cbc:ChargeIndicator>false</cbc:ChargeIndicator>\n" +
            "      <cbc:AllowanceChargeReason>Treuerabatt</cbc:AllowanceChargeReason>\n" +
            "      <cbc:Amount currencyID=\"EUR\">10.00</cbc:Amount>\n" +
            "      <cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19</cbc:Percent><cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory>\n" +
            "   </cac:AllowanceCharge>\n";

        private const string ChargeWithoutCodeAndBase =
            "   <cac:AllowanceCharge>\n" +
            "      <cbc:ChargeIndicator>true</cbc:ChargeIndicator>\n" +
            "      <cbc:AllowanceChargeReason>Fracht</cbc:AllowanceChargeReason>\n" +
            "      <cbc:Amount currencyID=\"EUR\">5.00</cbc:Amount>\n" +
            "      <cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19</cbc:Percent><cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory>\n" +
            "   </cac:AllowanceCharge>\n";


        private InvoiceDescriptor _Load(string insertBeforeTaxTotal)
        {
            string path = _makeSurePathIsCrossPlatformCompatible(@"..\..\..\..\demodata\xRechnung\xRechnung UBL.xml");
            string xml = File.ReadAllText(path, Encoding.UTF8).Replace("\r\n", "\n");
            int at = xml.IndexOf(TaxTotal + "\n", System.StringComparison.Ordinal);
            Assert.IsGreaterThan(0, at, "sample must contain the document-level TaxTotal");
            xml = xml.Insert(at, insertBeforeTaxTotal);
            using (MemoryStream stream = new MemoryStream(Encoding.UTF8.GetBytes(xml)))
            {
                return InvoiceDescriptor.Load(stream);
            }
        }


        private static string _SaveAsCii(InvoiceDescriptor desc)
        {
            using (MemoryStream stream = new MemoryStream())
            {
                desc.Save(stream, ZUGFeRDVersion.Version23, Profile.Comfort);
                return Encoding.UTF8.GetString(stream.ToArray());
            }
        }


        [TestMethod]
        public void AllowanceWithoutReasonCodeAndBasisIsNotInvented()
        {
            InvoiceDescriptor desc = _Load(AllowanceWithoutCodeAndBase);
            Assert.HasCount(1, desc.GetTradeAllowances());
            TradeAllowance allowance = desc.GetTradeAllowances()[0];
            Assert.IsNull(allowance.ReasonCode, "no reason code in the document, none must be invented (was 41)");
            Assert.IsNull(allowance.BasisAmount, "no base amount in the document, none must be invented (was 0.00)");
            Assert.AreEqual(10m, allowance.ActualAmount);
            Assert.AreEqual("Treuerabatt", allowance.Reason);

            string cii = _SaveAsCii(desc);
            StringAssert.DoesNotMatch(cii, new System.Text.RegularExpressions.Regex("<ram:ReasonCode>41</ram:ReasonCode>"));
            StringAssert.DoesNotMatch(cii, new System.Text.RegularExpressions.Regex("<ram:BasisAmount>0\\.00</ram:BasisAmount>"));
        }


        [TestMethod]
        public void ChargeWithoutReasonCodeAndBasisIsNotInvented()
        {
            InvoiceDescriptor desc = _Load(ChargeWithoutCodeAndBase);
            Assert.HasCount(1, desc.GetTradeCharges());
            TradeCharge charge = desc.GetTradeCharges()[0];
            Assert.IsNull(charge.ReasonCode);
            Assert.IsNull(charge.BasisAmount);
            Assert.AreEqual(5m, charge.ActualAmount);
        }


        [TestMethod]
        public void EmptyProjectReferenceGivesNoProject()
        {
            // the sample contains <cac:ProjectReference><cbc:ID/></cac:ProjectReference>
            InvoiceDescriptor desc = _Load(string.Empty);
            Assert.IsNull(desc.SpecifiedProcuringProject);
            StringAssert.DoesNotMatch(_SaveAsCii(desc), new System.Text.RegularExpressions.Regex("SpecifiedProcuringProject"));
        }


        [TestMethod]
        public void ProjectReferenceIsStillRead()
        {
            InvoiceDescriptor desc = _Load(string.Empty);
            string path = _makeSurePathIsCrossPlatformCompatible(@"..\..\..\..\demodata\xRechnung\xRechnung UBL.xml");
            string xml = File.ReadAllText(path, Encoding.UTF8).Replace("<cac:ProjectReference>\r\n      <cbc:ID/>", "<cac:ProjectReference>\r\n      <cbc:ID>PRJ-7</cbc:ID>")
                                                              .Replace("<cac:ProjectReference>\n      <cbc:ID/>", "<cac:ProjectReference>\n      <cbc:ID>PRJ-7</cbc:ID>");
            StringAssert.Contains(xml, "PRJ-7");
            using (MemoryStream stream = new MemoryStream(Encoding.UTF8.GetBytes(xml)))
            {
                desc = InvoiceDescriptor.Load(stream);
            }
            Assert.IsNotNull(desc.SpecifiedProcuringProject);
            Assert.AreEqual("PRJ-7", desc.SpecifiedProcuringProject.ID);
        }
    }
}
