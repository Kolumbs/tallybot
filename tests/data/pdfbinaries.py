"""PDF data binaries."""

BLANK_PAGE_PDF = b"""%PDF-1.1
1 0 obj
<< /Type /Catalog
   /Pages 2 0 R
>>
endobj

2 0 obj
<< /Type /Pages
   /Kids [3 0 R]
   /Count 1
>>
endobj

3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources <<
   >>
>>
endobj

4 0 obj
<< /Length 0 >>
stream
endstream
endobj

xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000079 00000 n
0000000138 00000 n
0000000260 00000 n
trailer
<< /Size 5
   /Root 1 0 R
>>
startxref
318
%%EOF"""
