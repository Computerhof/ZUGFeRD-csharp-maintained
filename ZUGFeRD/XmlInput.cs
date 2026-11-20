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
using System;
using System.IO;
using System.Text;
using System.Xml;

namespace s2industries.ZUGFeRD
{
    /// <summary>
    /// The only place where invoice XML is read. DTDs are prohibited (no entity expansion, no external resources) and the
    /// version is detected by streaming, without copying the document into memory.
    /// </summary>
    internal static class XmlInput
    {
        /// <summary>Upper bound for remembered candidate values during detection (memory limit for hostile input).</summary>
        internal const int MaxCandidates = 10000;

        /// <summary>Candidate values longer than this are not identifiers and are not remembered.</summary>
        internal const int MaxCandidateLength = 1000;

        private const int DoctypeLookahead = 64 * 1024;


        internal static XmlReaderSettings SafeSettings()
        {
            return new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit,
                XmlResolver = null,
                CloseInput = false,
                IgnoreComments = true,
                IgnoreProcessingInstructions = true
            };
        } // !SafeSettings()


        /// <summary>
        /// Loads the document from the current stream position. A document with a DOCTYPE raises an XmlException.
        /// Uses XmlTextReader like XmlDocument.Load(Stream) did before, so text content (e.g. line breaks) is unchanged;
        /// only DTD processing and the resolver are switched off. The reader is not disposed: that would close the
        /// caller's stream.
        /// </summary>
        internal static XmlDocument LoadDocument(Stream stream)
        {
            XmlDocument doc = new XmlDocument { XmlResolver = null };
            XmlTextReader reader = new XmlTextReader(stream, doc.NameTable)
            {
                DtdProcessing = DtdProcessing.Prohibit,
                XmlResolver = null
            };
            doc.Load(reader);
            return doc;
        } // !LoadDocument()


        /// <summary>
        /// Collects all text and attribute values that start with "urn" (spaces removed, lower case) from the whole stream,
        /// then restores the stream position. Matches the former detection (text of an element or value of an attribute equal
        /// to a known URI) without reading the document into a string.
        /// Malformed XML ends the scan silently (the caller then reports an unsupported document, as before); a DOCTYPE raises
        /// an XmlException.
        /// </summary>
        internal static XmlSniffResult Sniff(Stream stream)
        {
            XmlSniffResult result = new XmlSniffResult();
            long oldStreamPosition = stream.Position;
            stream.Position = 0;
            bool sawElement = false;
            try
            {
                using (XmlReader reader = XmlReader.Create(stream, SafeSettings()))
                {
                    while (reader.Read())
                    {
                        switch (reader.NodeType)
                        {
                            case XmlNodeType.Element:
                                sawElement = true;
                                while (reader.MoveToNextAttribute())
                                {
                                    result.AddAttributeValue(_Normalize(reader.Value));
                                }
                                break;
                            case XmlNodeType.Text:
                            case XmlNodeType.CDATA:
                                result.AddText(_Normalize(reader.Value));
                                break;
                        }
                    }
                }
            }
            catch (XmlException)
            {
                if (!sawElement && _HasDoctype(stream))
                {
                    stream.Position = oldStreamPosition;
                    throw new XmlException("DTD is not allowed in invoice documents (DOCTYPE found).");
                }
                // malformed document: keep what was collected so far
            }

            stream.Position = oldStreamPosition;
            return result;
        } // !Sniff()


        private static string _Normalize(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length > MaxCandidateLength)
            {
                return null;
            }

            string normalized = value.Replace(" ", String.Empty);
            if (!normalized.StartsWith("urn", StringComparison.OrdinalIgnoreCase))
            {
                return null;
            }
            return normalized.ToLowerInvariant();
        } // !_Normalize()


        private static bool _HasDoctype(Stream stream)
        {
            stream.Position = 0;
            using (StreamReader reader = new StreamReader(stream, Encoding.UTF8, true, 4096, true))
            {
                char[] buffer = new char[DoctypeLookahead];
                int read = reader.ReadBlock(buffer, 0, buffer.Length);
                return new string(buffer, 0, read).IndexOf("<!DOCTYPE", StringComparison.Ordinal) >= 0;
            }
        } // !_HasDoctype()
    }
}
