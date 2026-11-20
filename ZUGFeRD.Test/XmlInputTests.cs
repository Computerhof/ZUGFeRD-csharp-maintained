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
using System.IO;
using System.Text;
using System.Xml;

namespace s2industries.ZUGFeRD.Test
{
    /// <summary>
    /// Hardening of the XML input (maintenance fork): no DTD processing, version detection without copying the document.
    /// </summary>
    [TestClass]
    public class XmlInputTests : TestBase
    {
        private const string XmlDeclaration = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>";

        private string _Sample()
        {
            string path = _makeSurePathIsCrossPlatformCompatible(@"..\..\..\..\demodata\xRechnung\xRechnung CII.xml");
            string xml = File.ReadAllText(path, Encoding.UTF8);
            Assert.IsTrue(xml.StartsWith(XmlDeclaration), "sample must start with the XML declaration");
            return xml;
        }


        private string _WithDoctype(string doctype, string replaceTextWith = null)
        {
            string xml = _Sample();
            xml = XmlDeclaration + doctype + xml.Substring(XmlDeclaration.Length);
            if (replaceTextWith != null)
            {
                string marker = "<ram:ID>0815-99-1-a</ram:ID>";
                Assert.IsTrue(xml.Contains(marker), "sample must contain the invoice number");
                xml = xml.Replace(marker, "<ram:ID>" + replaceTextWith + "</ram:ID>");
            }
            return xml;
        }


        private static MemoryStream _Stream(string xml)
        {
            return new MemoryStream(Encoding.UTF8.GetBytes(xml));
        }


        [TestMethod]
        public void SampleStillLoads()
        {
            using (MemoryStream stream = _Stream(_Sample()))
            {
                Assert.AreEqual(ZUGFeRDVersion.Version23, InvoiceDescriptor.GetVersion(stream));
                Assert.AreEqual(0, stream.Position, "detection must restore the stream position");
                Assert.IsNotNull(InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void InternalEntityIsRejected()
        {
            string xml = _WithDoctype("<!DOCTYPE rsm:CrossIndustryInvoice [<!ENTITY e \"Injected\">]>", "&e;");
            using (MemoryStream stream = _Stream(xml))
            {
                Assert.ThrowsExactly<XmlException>(() => InvoiceDescriptor.GetVersion(stream));
                Assert.ThrowsExactly<XmlException>(() => InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void ExternalEntityIsRejected()
        {
            string xml = _WithDoctype("<!DOCTYPE rsm:CrossIndustryInvoice [<!ENTITY x SYSTEM \"file:///c:/windows/win.ini\">]>", "&x;");
            using (MemoryStream stream = _Stream(xml))
            {
                Assert.ThrowsExactly<XmlException>(() => InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void EntityExpansionIsRejected()
        {
            StringBuilder dtd = new StringBuilder("<!DOCTYPE rsm:CrossIndustryInvoice [<!ENTITY a0 \"lol\">");
            for (int i = 1; i <= 9; i++)
            {
                dtd.Append($"<!ENTITY a{i} \"&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};&a{i - 1};\">");
            }
            dtd.Append("]>");
            using (MemoryStream stream = _Stream(_WithDoctype(dtd.ToString(), "&a9;")))
            {
                Assert.ThrowsExactly<XmlException>(() => InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void DoctypeInFileIsRejected()
        {
            string file = Path.GetTempFileName();
            try
            {
                File.WriteAllText(file, _WithDoctype("<!DOCTYPE rsm:CrossIndustryInvoice []>"), Encoding.UTF8);
                Assert.ThrowsExactly<XmlException>(() => InvoiceDescriptor.Load(file));
            }
            finally
            {
                File.Delete(file);
            }
        }


        [TestMethod]
        public void NonXmlIsStillUnsupported()
        {
            using (MemoryStream stream = _Stream("%PDF-1.7 this is not xml"))
            {
                Assert.ThrowsExactly<UnsupportedException>(() => InvoiceDescriptor.GetVersion(stream));
                Assert.ThrowsExactly<UnsupportedException>(() => InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void UnknownDocumentIsStillUnsupported()
        {
            using (MemoryStream stream = _Stream("<root><id>urn:example:unknown</id></root>"))
            {
                Assert.ThrowsExactly<UnsupportedException>(() => InvoiceDescriptor.Load(stream));
            }
        }


        [TestMethod]
        public void DetectionDoesNotCopyTheDocument()
        {
            // 20 MB of padding: the former detection read the whole stream into strings once per reader (about 26 times the
            // input in total). Streaming detection must stay well below the input size.
            string sample = _Sample();
            string padding = "<!--" + new string('x', 20 * 1024 * 1024) + "-->";
            byte[] bytes = Encoding.UTF8.GetBytes(XmlDeclaration + padding + sample.Substring(XmlDeclaration.Length));

            using (MemoryStream stream = new MemoryStream(bytes))
            {
                long before = GC.GetAllocatedBytesForCurrentThread();
                Assert.AreEqual(ZUGFeRDVersion.Version23, InvoiceDescriptor.GetVersion(stream));
                long allocated = GC.GetAllocatedBytesForCurrentThread() - before;
                Assert.IsTrue(allocated < bytes.Length, $"detection allocated {allocated:N0} bytes for {bytes.Length:N0} bytes input");
            }
        }
    }
}
