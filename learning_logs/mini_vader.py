import re
import math
from collections import defaultdict

class MiniVader:
    def __init__(self, lexicon=None):
        # Small sample lexicon. Extend this with more words or load from file.
        self.lexicon = lexicon or {
            "good": 2.0, "great": 3.0, "excellent": 4.0, "amazing": 3.5, "love": 3.0,
            "happy": 2.0, "nice": 1.5,
            "bad": -2.0, "terrible": -3.5, "awful": -3.0, "hate": -3.0, "worst": -4.0,
            "sad": -2.0, "disappointing": -2.0,
            # add more words for better coverage
        }

        # Intensifiers: multiplier applied to words after them
        self.intensifiers = {
            "very": 1.5, "extremely": 2.0, "so": 1.3, "really": 1.4, "too": 1.2, "slightly": 0.8
        }

        # Negations flip the polarity of the following sentiment-bearing word(s)
        self.negations = {"not", "never", "no", "n't", "cannot", "can't", "dont", "don't"}

        # Basic emoji mapping (extend as needed)
        self.emoji_lexicon = {
            "😊": 2.0, "🙂": 1.5, "😍": 3.0, "😁": 2.0,
            "😢": -2.0, "😠": -2.5, "😡": -3.0, "😭": -3.0
        }

        # punctuation boost factors
        self.exclam_boost = 0.2   # per '!' (capped)
        self.question_boost = 0.1 # per '?', small effect

        # caps boost multiplier
        self.caps_boost = 1.5

    def _tokenize(self, text):
        # preserve emojis by not stripping non-word emojis
        # split on whitespace and punctuation, keep words and emojis
        tokens = re.findall(r"\w+|[!?.]+|[\u2600-\u27BF\u1F300-\u1F6FF\u1F900-\u1F9FF]+", text)
        return tokens

    def _count_exclamation_question(self, text):
        ex = text.count('!')
        q = text.count('?')
        return ex, q

    def _is_all_caps(self, token):
        # consider as caps if token has letters and is all uppercase with length>1
        return any(c.isalpha() for c in token) and token.isupper() and len(token) > 1

    def _normalize_score(self, raw_score):
        # VADER-style normalization to compound score between -1 and +1
        # Using same style formula: compound = raw / sqrt(raw^2 + alpha)
        alpha = 15.0
        if raw_score == 0:
            return 0.0
        compound = raw_score / math.sqrt(raw_score * raw_score + alpha)
        # clamp just in case
        if compound > 1.0: compound = 1.0
        if compound < -1.0: compound = -1.0
        return compound

    def analyze(self, text):
        """
        Returns a dict:
        {
          "compound": float between -1..1,
          "label": "positive"/"negative"/"neutral",
          "pos": total_pos_score,
          "neg": total_neg_score,
          "neu": neutral_count
        }
        """
        if not text or not text.strip():
            return {"compound": 0.0, "label": "neutral", "pos": 0.0, "neg": 0.0, "neu": 0}

        # Preprocessing
        orig_text = text
        tokens = self._tokenize(text)
        words = [t for t in tokens if re.match(r"\w+", t)]
        ex_count, q_count = self._count_exclamation_question(text)

        raw_score = 0.0
        pos_score = 0.0
        neg_score = 0.0
        neu_count = 0

        negate_next = False
        i = 0
        n = len(tokens)

        # handle "but" clauses: split at 'but' and weight second part higher
        # find index of largest contrastive 'but' (lowercase compare)
        lower = orig_text.lower()
        if " but " in lower:
            parts = re.split(r"\bbut\b", orig_text, flags=re.IGNORECASE)
            # analyze separately with weights: first 0.5, second 1.5
            first = parts[0].strip()
            second = parts[1].strip() if len(parts) > 1 else ""
            score_first = self._score_plain(first)
            score_second = self._score_plain(second)
            combined = score_first * 0.5 + score_second * 1.5
            compound = self._normalize_score(combined)
            label = "positive" if compound > 0.05 else "negative" if compound < -0.05 else "neutral"
            return {"compound": compound, "label": label, "pos": max(0, combined), "neg": max(0, -combined), "neu": 0}

        # fallback to single-pass scoring if no 'but' clause
        # we'll implement scoring inline here using helper for intensifiers and emojis
        while i < n:
            token = tokens[i]
            lower_token = token.lower()

            # emojis lookup
            if token in self.emoji_lexicon:
                val = self.emoji_lexicon[token]
                raw_score += val
                if val > 0: pos_score += val
                else: neg_score += -val
                i += 1
                continue

            # punctuation tokens just skip (we use punctuation boost later)
            if re.fullmatch(r"[!?.]+", token):
                i += 1
                continue

            # negation handling
            if lower_token in self.negations:
                negate_next = True
                i += 1
                continue

            # intensifier handling: if current token is an intensifier, lookahead to next word
            if lower_token in self.intensifiers:
                multiplier = self.intensifiers[lower_token]
                # lookahead for sentiment-bearing word within next 2 tokens
                j = i + 1
                applied = False
                while j < n and j <= i + 2:
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
                    # no sentiment word found; just skip intensifier
                    i += 1
                    continue

            # normal word sentiment lookup
            if lower_token in self.lexicon:
                v = self.lexicon[lower_token]
                # caps boost if token in all caps (shouted)
                if self._is_all_caps(token):
                    v *= self.caps_boost
                if negate_next:
                    v = -v
                    negate_next = False
                raw_score += v
                if v > 0:
                    pos_score += v
                else:
                    neg_score += -v
            else:
                neu_count += 1
            i += 1

        # punctuation boosting (exclamation / question)
        # cap exclamation effect to avoid runaway boosting
        ex_boost_total = min(ex_count, 4) * self.exclam_boost
        q_boost_total = min(q_count, 4) * self.question_boost
        raw_score *= (1.0 + ex_boost_total + q_boost_total)

        compound = self._normalize_score(raw_score)
        label = "positive" if compound > 0.05 else "negative" if compound < -0.05 else "neutral"
        return {"compound": compound, "label": label, "pos": pos_score, "neg": neg_score, "neu": neu_count}

    def _score_plain(self, text):
        """
        Helper that returns raw score for a plain text (no 'but' splitting).
        This duplicates a subset of analyze logic but returns raw_score for weighted mixing.
        """
        tokens = self._tokenize(text)
        n = len(tokens)
        i = 0
        raw_score = 0.0
        negate_next = False
        while i < n:
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
            if lower_token in self.intensifiers:
                multiplier = self.intensifiers[lower_token]
                # lookahead
                j = i + 1
                applied = False
                while j < n and j <= i + 2:
                    cand = tokens[j].lower()
                    if cand in self.lexicon:
                        v = self.lexicon[cand] * multiplier
                        if self._is_all_caps(tokens[j]):
                            v *= self.caps_boost
                        if negate_next:
                            v = -v
                            negate_next = False
                        raw_score += v
                        applied = True
                        break
                    j += 1
                if applied:
                    i = j + 1
                    continue
                else:
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
        # punctuation boosts
        ex_count, q_count = self._count_exclamation_question(text)
        raw_score *= (1.0 + min(ex_count, 4) * self.exclam_boost + min(q_count, 4) * self.question_boost)
        return raw_score
