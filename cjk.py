import codecs
import re

u_code_re = re.compile(r'^U\+([0-9a-fA-F]+)$')

def parse_u_code(u_code):
  """Parses a string in the format U+XXXX and returns the numeric code."""
  m = u_code_re.match(u_code)
  return int(m.group(1), 16)

def get_conv_table():
  """
  Parse the unihan.txt file and generate a conversion table between
  unicode ord value and pinyin transliteration.
  Note that this only makes sense with a cleaned-up unihan.txt file,
  which only contains one character per ord value. It has been tested
  with a file containing only the 'kMandarin' codes.
  """
  conv_table = {}
  pinyin_table_filename = 'pinyin.txt'
  with codecs.open(pinyin_table_filename, encoding='utf-8') as f:
    for line in f:
      (u_code, _, pinyin) = line.split()
      char_code = parse_u_code(u_code)
      conv_table[char_code] = pinyin
  return conv_table


def isCharacterCJK(c):
  """
  Check that the character c is in the range for CJK unicode characters, according to this table:

  Block                                   Range       Comment
  CJK Unified Ideographs                  4E00-9FFF   Common
  CJK Unified Ideographs Extension A      3400-4DFF   Rare
  CJK Unified Ideographs Extension B      20000-2A6DF Rare, historic
  CJK Compatibility Ideographs            F900-FAFF   Duplicates, unifiable variants, corporate characters
  CJK Compatibility Ideographs Supplement 2F800-2FA1F Unifiable variants

  However since we're probably interested only in UCS2 characters, we'll skip anything above 0x10000.
  """
  ord_c = ord(c)
  if ord_c < 0x3400:
    return False
  if ord_c > 0x9fff and ord_c < 0xf900:
    return False
  if ord_c > 0xfaff:
    return False
  return True


def testIsCharacterCJK():
  assert isCharacterCJK('a') == False
  assert isCharacterCJK(u'\u3100') == False
  assert isCharacterCJK(u'\u3899') == True
  assert isCharacterCJK(u'\u4e01') == True
  assert isCharacterCJK(u'\u8888') == True
  assert isCharacterCJK(u'\uaaaa') == False
  assert isCharacterCJK(u'\ufa23') == True
  assert isCharacterCJK(u'\ufd00') == False


if __name__ == "__main__":
  testIsCharacterCJK()

