import re
import math
from collections import defaultdict

class MiniVader:
    def __init__(self, lexicon=None):
        # sample lexicon, now supports multiword phrases in lowercase
        self.lexicon = lexicon or {
            "good": 2.0, "great": 3.0, "excellent": 4.0, "amazing": 3.5, "love": 3.0,
            "happy": 2.0, "nice": 1.5, "decent": 1.5,"beautiful":2.5,
            "bad": -2.0, "terrible": -3.5, "awful": -3.0, "hate": -3.0, "worst": -4.0,
            "sad": -2.0, "disappointing": -2.0,

            # ✅ example multi-grams (you can add more)
            "not good": -2.5,
            "very good": 3.0,
            "really love": 3.5,
            "kind of bad": -1.5,
            "not at all good": -3.2
        }

        self.intensifiers = {
            "very": 1.5, "extremely": 2.0, "so": 1.3, "really": 1.4, "too": 1.2, "slightly": 0.8
        }

        self.negations = {"not", "never", "no", "n't", "cannot", "can't", "dont", "don't"}

        self.emoji_lexicon = {
            "😊": 2.0, "🙂": 1.5, "😍": 3.0, "😁": 2.0,
            "😢": -2.0, "😠": -2.5, "😡": -3.0, "😭": -3.0
        }

        self.exclam_boost = 0.2
        self.question_boost = 0.1
        self.caps_boost = 1.5
        self.max_phrase_len = 3   # ✅ sliding window 1-gram, 2-gram, 3-gram

    def _tokenize(self, text):
        return re.findall(r"\w+|[!?.]+|[\u2600-\u27BF\u1F300-\u1F6FF\u1F900-\u1F9FF]+", text)

    def _count_exclamation_question(self, text):
        return text.count('!'), text.count('?')

    def _is_all_caps(self, token):
        return any(c.isalpha() for c in token) and token.isupper() and len(token) > 1

    def _normalize_score(self, raw_score):
        alpha = 15.0
        if raw_score == 0:
            return 0.0
        compound = raw_score / math.sqrt(raw_score * raw_score + alpha)
        return max(min(compound, 1.0), -1.0)

    def _match_phrase(self, tokens, i):
        """
        Sliding window matcher: tries 3-gram, then 2-gram, ignores punctuation,
        returns (phrase, length) or (None, 1)
        """
        phrase_tokens = []
        idx = i
        used = 0

        while idx < len(tokens) and used < self.max_phrase_len:
            if not re.match(r"\w+", tokens[idx]):  # skip punctuation/emojis in phrase build
                idx += 1
                continue

            phrase_tokens.append(tokens[idx].lower())
            used += 1
            phrase = " ".join(phrase_tokens)

            if phrase in self.lexicon and used > 1:  # only accept 2+ words as phrase
                return phrase, idx - i + 1

            idx += 1

        return None, 1  # no phrase match → process normally as 1 token

    def analyze(self, text):
        if not text or not text.strip():
            return {"compound": 0.0, "label": "neutral", "pos": 0.0, "neg": 0.0, "neu": 0}

        orig_text = text
        tokens = self._tokenize(text)
        ex_count, q_count = self._count_exclamation_question(text)

        raw_score = 0.0
        pos_score = 0.0
        neg_score = 0.0
        neu_count = 0
        negate_next = False
        i = 0

        # handle "but" clauses
        if " but " in orig_text.lower():
            parts = re.split(r"\bbut\b", orig_text, flags=re.IGNORECASE)
            first = parts[0].strip()
            second = parts[1].strip() if len(parts) > 1 else ""
            score_first = self._score_plain(first)
            score_second = self._score_plain(second)
            combined = score_first * 0.5 + score_second * 1.5
            compound = self._normalize_score(combined)
            label = "positive" if compound > 0.05 else "negative" if compound < -0.05 else "neutral"
            return {"compound": compound, "label": label, "pos": max(0, combined), "neg": max(0, -combined), "neu": 0}

        while i < len(tokens):
            token = tokens[i]
            lower_token = token.lower()

            # ✅ Multi-gram phrase matching
            phrase, skip = self._match_phrase(tokens, i)
            if phrase:
                v = self.lexicon[phrase]
                if negate_next:
                    v = -v
                    negate_next = False
                raw_score += v
                if v > 0: pos_score += v
                else: neg_score += -v
                i += skip
                continue

            # emoji
            if token in self.emoji_lexicon:
                val = self.emoji_lexicon[token]
                raw_score += val
                if val > 0: pos_score += val
                else: neg_score += -val
                i += 1
                continue

            # punctuation
            if re.fullmatch(r"[!?.]+", token):
                i += 1
                continue

            # negation
            if lower_token in self.negations:
                negate_next = True
                i += 1
                continue

            # intensifier
            if lower_token in self.intensifiers:
                multiplier = self.intensifiers[lower_token]
                j = i + 1
                applied = False
                while j < len(tokens) and j <= i + 2:
                    cand = tokens[j].lower()
                    if cand in self.lexicon:
                        v = self.lexicon[cand] * multiplier
                        if self._is_all_caps(tokens[j]):
                            v *= self.caps_boost
                        if negate_next:
                            v = -v
                            negate_next = False
                        raw_score += v
                        if v > 0: pos_score += v
                        else: neg_score += -v
                        applied = True
                        break
                    j += 1
                if applied:
                    i = j + 1
                    continue
                else:
                    i += 1
                    continue

            # normal word
            if lower_token in self.lexicon:
                v = self.lexicon[lower_token]
                if self._is_all_caps(token):
                    v *= self.caps_boost
                if negate_next:
                    v = -v
                    negate_next = False
                raw_score += v
                if v > 0: pos_score += v
                else: neg_score += -v
            else:
                neu_count += 1
            i += 1

        raw_score *= (1.0 + min(ex_count, 4) * self.exclam_boost +
                      min(q_count, 4) * self.question_boost)

        compound = self._normalize_score(raw_score)
        label = "positive" if compound > 0.05 else "negative" if compound < -0.05 else "neutral"
        return {"compound": compound, "label": label, "pos": pos_score, "neg": neg_score, "neu": neu_count}

    def _score_plain(self, text):
        tokens = self._tokenize(text)
        i = 0
        raw_score = 0.0
        negate_next = False

        while i < len(tokens):
            phrase, skip = self._match_phrase(tokens, i)
            if phrase:
                v = self.lexicon[phrase]
                if negate_next:
                    v = -v
                    negate_next = False
                raw_score += v
                i += skip
                continue

            token = tokens[i]
            lower_token = token.lower()

            if token in self.emoji_lexicon:
                raw_score += self.emoji_lexicon[token]
                i += 1
                continue
            if re.fullmatch(r"[!?.]+", token):
                i += 1
                continue
            if lower_token in self.negations:
                negate_next = True
                i += 1
                continue
            if lower_token in self.lexicon:
                v = self.lexicon[lower_token]
                if self._is_all_caps(token):
                    v *= self.caps_boost
                if negate_next:
                    v = -v
                    negate_next = False
                raw_score += v
            i += 1

        ex_count, q_count = self._count_exclamation_question(text)
        raw_score *= (1.0 + min(ex_count, 4) * self.exclam_boost +
                      min(q_count, 4) * self.question_boost)
        return raw_score
