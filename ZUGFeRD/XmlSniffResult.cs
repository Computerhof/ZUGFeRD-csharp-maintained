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
using System.Collections.Generic;

namespace s2industries.ZUGFeRD
{
    /// <summary>
    /// Candidate identifiers found in a document (see XmlInput.Sniff): element texts and attribute values starting with
    /// "urn", spaces removed, lower case. Bounded in number so hostile input cannot grow it without limit.
    /// </summary>
    internal sealed class XmlSniffResult
    {
        private readonly HashSet<string> _Texts = new HashSet<string>();
        private readonly HashSet<string> _AttributeValues = new HashSet<string>();


        internal void AddText(string normalized)
        {
            if (normalized != null && _Texts.Count < XmlInput.MaxCandidates)
            {
                _Texts.Add(normalized);
            }
        } // !AddText()


        internal void AddAttributeValue(string normalized)
        {
            if (normalized != null && _AttributeValues.Count < XmlInput.MaxCandidates)
            {
                _AttributeValues.Add(normalized);
            }
        } // !AddAttributeValue()


        /// <summary>True if an element text equals one of the URIs (case-insensitive, spaces ignored).</summary>
        internal bool ContainsText(IEnumerable<string> uris)
        {
            return _ContainsAny(_Texts, uris);
        } // !ContainsText()


        /// <summary>True if an attribute value (e.g. a namespace declaration) equals one of the URIs.</summary>
        internal bool ContainsAttributeValue(IEnumerable<string> uris)
        {
            return _ContainsAny(_AttributeValues, uris);
        } // !ContainsAttributeValue()


        private static bool _ContainsAny(HashSet<string> values, IEnumerable<string> uris)
        {
            foreach (string uri in uris)
            {
                if (values.Contains(uri.Replace(" ", string.Empty).ToLowerInvariant()))
                {
                    return true;
                }
            }
            return false;
        } // !_ContainsAny()
    }
}
