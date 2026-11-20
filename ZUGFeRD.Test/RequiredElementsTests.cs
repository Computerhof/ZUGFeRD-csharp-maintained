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
using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
using System.Xml.Schema;

namespace s2industries.ZUGFeRD.Test
{
    /// <summary>
    /// Elements the CII schema requires even when they carry no data (maintenance fork).
    /// </summary>
    [TestClass]
    public class RequiredElementsTests : TestBase
    {
        private readonly InvoiceProvider _InvoiceProvider = new InvoiceProvider();

        private const string Ram = "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100";


        private InvoiceDescriptor _InvoiceWithoutDelivery()
        {
            InvoiceDescriptor desc = _InvoiceProvider.CreateInvoice();
            desc.ActualDeliveryDate = null;
            Assert.IsNull(desc.ShipTo);
            Assert.IsNull(desc.DeliveryNoteReferencedDocument);
            Assert.IsNull(desc.DespatchAdviceReferencedDocument);
            return desc;
        }


        private static XmlDocument _Save(InvoiceDescriptor desc, ZUGFeRDVersion version, Profile profile)
        {
            using (MemoryStream stream = new MemoryStream())
            {
                desc.Save(stream, version, profile);
                stream.Position = 0;
                XmlDocument doc = new XmlDocument();
                doc.Load(stream);
                return doc;
            }
        }


        private static XmlNode _Delivery(XmlDocument doc)
        {
            XmlNamespaceManager nsmgr = new XmlNamespaceManager(doc.NameTable);
            nsmgr.AddNamespace("ram", Ram);
            return doc.SelectSingleNode("//ram:ApplicableHeaderTradeDelivery", nsmgr);
        }


        [TestMethod]
        public void DeliveryIsWrittenWithoutDeliveryDataVersion23()
        {
            XmlDocument doc = _Save(_InvoiceWithoutDelivery(), ZUGFeRDVersion.Version23, Profile.Comfort);
            XmlNode delivery = _Delivery(doc);
            Assert.IsNotNull(delivery, "ram:ApplicableHeaderTradeDelivery is required by CII D16B/D22B");
            Assert.IsFalse(delivery.HasChildNodes);

            string schemaPath = _makeSurePathIsCrossPlatformCompatible(@"..\..\..\..\documentation\zugferd233de\Schema\3. Factur-X_1.07.3_EN16931\Factur-X_1.07.3_EN16931.xsd");
            XmlSchemaSet schemas = new XmlSchemaSet { XmlResolver = new XmlUrlResolver() };
            schemas.Add(null, schemaPath);
            doc.Schemas.Add(schemas);
            List<string> errors = new List<string>();
            doc.Validate((sender, args) => errors.Add(args.Message));
            Assert.IsEmpty(errors, String.Join(Environment.NewLine, errors));
        }


        [TestMethod]
        public void DeliveryIsWrittenWithoutDeliveryDataVersion20()
        {
            XmlDocument doc = _Save(_InvoiceWithoutDelivery(), ZUGFeRDVersion.Version20, Profile.Comfort);
            Assert.IsNotNull(_Delivery(doc));
        }


        [TestMethod]
        public void DeliveryDataIsStillWritten()
        {
            InvoiceDescriptor desc = _InvoiceWithoutDelivery();
            desc.ActualDeliveryDate = new DateTime(2026, 11, 2);
            XmlNode delivery = _Delivery(_Save(desc, ZUGFeRDVersion.Version23, Profile.Comfort));
            Assert.IsNotNull(delivery);
            StringAssert.Contains(delivery.InnerText, "20261102");
        }
    }
}
