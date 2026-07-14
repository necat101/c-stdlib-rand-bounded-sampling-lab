# HN thread 17599660: Efficiently Generating a Number in a Range

URL: https://news.ycombinator.com/item?id=17599660
Article: http://www.pcg-random.org/posts/bounded-rands.html

## 17609054 by sdmike1

Personally I&#x27;m a fan of the xoshiro[1] generator I have found it to be faster and give more equiprobable outputs.<p>[1]<a href="http:&#x2F;&#x2F;xoshiro.di.unimi.it" rel="nofollow">http:&#x2F;&#x2F;xoshiro.di.unimi.it</a>

## 17609104 by nerdponx

This is well-timed. I don&#x27;t know much about different random number generators but I do know that we recently had an problem where RNG was a serious performance bottleneck.

## 17609614 by dahart

The article discusses the xoshiro RNG, and some better alternatives: “One other concern we might have is that some generators have weak low-order bits. For example, the Xoroshiro+ and Xoshiro+ families of PRNGs have low-order bits that fail statistical tests.“<p>The xoshiro page mentions this too, and says it won’t matter if you are generating random floats, but the article is generating random ints.<p>The RNG isn’t the point of the article though. It’s discussing the speed and correctness of what happens after the RNG but before you use the results.

## 17610014 by throwaway080383

Note that this article is not about the random number generating scheme, but about post-processing to get a random number within a certain range. That said, the author specifically points out xoshiro as a random number generating scheme to watch out for:<p><i>One other concern we might have is that some generators have weak low-order bits. For example, the Xoroshiro+ and Xoshiro+ families of PRNGs have low-order bits that fail statistical tests. When we perform % 52 (because 52 is even) we pass the lowest bit straight through into the output.</i>

## 17610117 by smaddox

xoshiro has flaws: <a href="http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;a-quick-look-at-xoshiro256.html" rel="nofollow">http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;a-quick-look-at-xoshiro256.h...</a>

## 17610205 by dagenix

&gt; Let&#x27;s move from an over-engineered approach to an under-engineered one.<p>The article says this to deride C++s implementation as being too complicated because it supports ranges such as [-3,17] and then promptly goes on to discuss how a modulo based implementation is very biased if the upper end of the range is above 2^31. It&#x27;s not really clear why the former use case is unimportant but the latter isn&#x27;t.<p>It just goes to show that one person&#x27;s niche use case is another person&#x27;s main use case. I wish people would just avoid the judgemental term &quot;over engineered&quot; and instead focus on matching appropriate algorithms to appropriate use cases.

## 17610210 by ?



## 17610299 by nightcracker

xoshiro&#x27;s response: <a href="http:&#x2F;&#x2F;pcg.di.unimi.it&#x2F;pcg.php" rel="nofollow">http:&#x2F;&#x2F;pcg.di.unimi.it&#x2F;pcg.php</a>

## 17610446 by smaddox

Interesting read, thanks! The deflection about xoshiro is not particularly convincing, though. It&#x27;s much more likely that you&#x27;ll want to multiply your random stream by a multiple of 57 than you&#x27;ll want to xor it with a 43-bit-shifted version of itself. He also doesn&#x27;t appear to counter the complaint about the generator getting stuck around 0: <a href="http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;xoshiro-repeat-flaws.html" rel="nofollow">http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;xoshiro-repeat-flaws.html</a><p>The other parts of the post definitely concern me about using the PCG&#x27;s described, though. Also, it&#x27;s interesting to see how PCG can be predicted. I would not have known how to attack it.

## 17610542 by simias

Note that this article is not really about RNGs themselves, but mostly how to use one to generate an unbiased number within a given range from a &quot;raw&quot; RNG output which typically generates a stream of 32 or 64bit integers.<p>Regarding the performance of RNGs themselves it&#x27;s mostly bound by how &quot;random&quot; your want your NG to be. If you don&#x27;t really care about quality and need very good performance, for instance to procedurally generate assets in a videogame, there are extremely fast and somewhat decent PRNGs out there, such as XorShift. Of course you won&#x27;t use that to generate PGP keys...

## 17610551 by WorkLifeBalance

The modulo approach is biased for all ranges which don&#x27;t divide the full range but only a small amount of bias at small ranges rather than a large amount of bias at large ranges.

## 17610571 by by

I only skimmed the article, so maybe they said this, but for choosing from a small range, for example 0..51, you can get several of these from a 32 bit random number with this algorithm<p><a href="https:&#x2F;&#x2F;stackoverflow.com&#x2F;questions&#x2F;6046918&#x2F;how-to-generate-a-random-integer-in-the-range-0-n-from-a-stream-of-random-bits&#x2F;10481147#10481147" rel="nofollow">https:&#x2F;&#x2F;stackoverflow.com&#x2F;questions&#x2F;6046918&#x2F;how-to-generate-...</a><p>You should be able to run a 64 bit PRNG once and pick at least 8 random cards from a deck.

## 17610610 by modeless

Melissa O&#x27;Neill&#x27;s response back: <a href="http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;on-vignas-pcg-critique.html" rel="nofollow">http:&#x2F;&#x2F;www.pcg-random.org&#x2F;posts&#x2F;on-vignas-pcg-critique.html</a>

## 17610626 by vinkelhake

The comment there is not about [-3, 17] being an obscure <i>output</i> range from a distribution. It is that the distribution must be able to handle a random generator that outputs numbers in that range.<p>I think there&#x27;s a small error there in that the output type of <i>UniformRandomBitGenerator</i> must be actually be unsigned. The larger point still stands though. It is possible to write a conforming <i>UniformRandomBitGenerator</i> that has an output range of [3, 17] and it falls on the distribution to handle this.

## 17610648 by rootlocus

<p><pre><code>    return min + (max - min) &#x2F; 2
</code></pre>
Oh, you want a random number?

## 17610662 by ballenf

The article&#x27;s conclusion was that the PRNG generation method used is usually not the bottleneck, but how you take that to get a result is. Don&#x27;t know if that applies to the algorithm linked, but the author&#x27;s point was that bottlenecks are more likely to arise in the code that surrounds the PRNG algorithm than in the call to PRNG itself.

## 17610786 by dagenix

I don&#x27;t disagree - I just very much hate the phrase &quot;over engineered&quot; as I think it never adds anything to a discussion.

## 17610799 by dagenix

Ah, good call. I did slightly misinterpret what was being said. I think my overall point still stands, though.

## 17610932 by smaddox

Thanks. This completely allays my concerns about the PCG&#x27;s I would actually use.<p>Edit: And I like that MCG with 64-bit multiplicand that she shows. I might switch to that for Monte Carlo applications.

## 17610982 by modeless

It seems crazy to me that there&#x27;s no way to produce unbiased numbers in an arbitrary range without rejection sampling and a loop. Is there a proof of this?

## 17611078 by kazinator

In TXR Lisp, the algorithm I put in place basically finds the tightest power-of-two bounding box for the modulus, clisp the pseudo-andom number to that power-of-two range, and then rejects values outside of the modulus.<p>Example: suppose we wanted values in the range 0 to 11. The tightest power of two is 16, so we generate 4 bit pseudo-random numbers in the 0 to 15 range. If we get a value in the 12 to 15 range, we throw it away and choose another one.<p>The clipping to the power-of-two bounding box ensures that we reject at most 50% of the raw values.<p>I don&#x27;t bother optimizing for small cases. That is, under this 4 bit example, each generated value that is trimmed to 4 bits will be the full output of the PRNG, a 32 bit value.  The approach pays off for bignums; the PRNG is called enough times to cover the bits, clipped to the power-of-two box, then subject to the rejection test.

## 17611105 by duckerude

I&#x27;d expect it&#x27;s possible by changing the generator at the lowest level, but it makes sense to me that you need a loop if you don&#x27;t control the underlying generator.<p>Imagine you want to turn a random number in 1..4 into a random number in 1..3. The original is your only source of randomness, so the rest should be deterministic. Then each outcome in 1..4 has to map to exactly one number in 1..3, but there&#x27;s no mapping that accepts all of 1..4 while still giving each of 1..3 an equal probability.

## 17611310 by modeless

What if we allow the mapping function to be stateful?

## 17611429 by frankmcsherry

You don&#x27;t need rejection sampling, but you do need a loop. It is easier to see that a finite number of samples is not sufficient:<p>If you have only a probability distribution defined by a product space where all distinguishable events have probability p^i, for some finite i, then any subset of the distinguishable events accumulate to a probability r * p^i for some integral r. If your goal is a probability that is not an integral multiple of p^i, you are out of luck with a finite number of samples.

## 17611438 by duckerude

I guess you could save up a few bits over repeated calls, but it can&#x27;t help you always execute the first call with a single round of generation.

## 17611569 by dragontamer

Trivial proof. Pigeon hole principle.<p>Double-precision Floats have more values between 0.0 and 1.0, than between 1.0 and 2.0. In fact, roughly half of ALL double-precision floats exist between -1.0 and 1.0, a very small minority of them exist between 1.0 and 2.0.<p>To generate unbiased random numbers between 0.0 and 2.0, it therefore requires you to either reject a significant amount of numbers in the 0.0 to 1.0 range, or perform some kind of many-to-few mapping in the 1.0 to 2.0 range.<p>----------<p>With regards to arbitrary INTEGER ranges, the proof is even easier. A random bitstream has 2^number-of-bits possible random values. Which does NOT divide evenly into an arbitrary integer range.<p>For example, 5-random bits will represent 32-different values. There&#x27;s no way to map 32-values and divide them evenly into 0-9 (10 numbers).

## 17611706 by modeless

Could it cap the maximum number of generator calls though? Rejection sampling is technically O(infinity) because you could reject an unbounded number of times. This isn&#x27;t a problem in practice but it sure is theoretically annoying. With a cap on the maximum number of calls, it would be O(1).

## 17611742 by zeeboo

His &quot;attack&quot; is literally a brute force of 32 bits of state. It would not scale to PCG with 128 bits of internal state.

## 17611751 by throwawaymath

Would you mind talking a little bit more about the scenario and bottleneck? If you&#x27;re concerned about anonymity you can just email me directly. I&#x27;m working on a research project to examine real world scenarios when the fastest cryptographic PRNGs are legitimately insufficient; your case might be useful.

## 17612214 by duckerude

I don&#x27;t think so.<p>If you want a number in 1..3, and the generator provides numbers from 1..4, and you want a cap n, then you could model it as a generator that provides numbers in 1..4^n. There&#x27;s never a way to split that space into three equal parts.<p>You always end up with unwanted extra possibilities that you still need to handle somehow.

## 17612553 by jgtrosh

Off the top of my head, for a randomly chosen range of size n, you reject a throw with probability 1&#x2F;4, right?

## 17612861 by throwaway080383

It&#x27;s unintuitive, but I believe the probability ends up being 1-ln(2) if you think of n as being uniformly random.

## 17612922 by dan-robertson

This is referred to as “Bitmask” in the article.

## 17613169 by dan-robertson

Proposition: There is no way, given some integer r and a sequence of iid random integer samples X1,X2,... uniformly distributed in [0,n) for some n&gt;1, to always construct some finite k and function f : [0,n)^k -&gt; [0,r) such that f(X1,...,Xk) is uniformly distributed over [0,r).<p>Proof: Suppose such a k and f exist. The distribution of U[0,n)^k is isomorphic to that of U[0,n^k) (just treat it like writing down a k-digit number in base n). And so f must be a function from a set of n^k  things to a set of r things. By the pigeonhole principle there must be some integers x,y in [0,r) such that the preimage of x has size at least ceiling(n^k&#x2F; r) and the preimage of y has size at most floor(n^k&#x2F; r). By the fundamental theorem of arithmetic there exists (for any n,k) some r such that n^k&#x2F;r is not an integer and so the probabilities of x,y (being proportional to the sizes of their fibres under f) are not equal.<p>————<p>The gist of this is that you always might need to loop (repeatedly sample) for some ranges and you might need to repeat arbitrarily many times.<p>One way is by rejection.<p>Another nice thing is if you want to generate a Bernoulli r.v. for some probability p a computable number, you lazily compute the bits of p simultaneously to a random sequence of bits (distributed as Bernoulli(1&#x2F;2)) and compare the two. If your random sequence is definitely less than p then generate 0. If definitely greater then generate 1. If not sure then generate some more bits.<p>In this way any Bernoulli random variable may be generated from an infinite sequence of iid Bernoulli(1&#x2F;2), and basically any probability space can be modelled in this way too. In this sense, all of probability can be built out of tosses of a fair coin)

## 17613362 by adrianmonk

I wonder if the &quot;Bitmask with Rejection&quot; method would be more efficient if you sometimes made the mask one bit larger than strictly necessary.<p>As it is, if you want a number in the range 0..8, you take 4 bits of randomness, giving you a number in 0..15. This is great, but 7&#x2F;16 (43.75%) of the time you have to try again. This not only means more loop iterations, it also means you discard 4 bits of randomness, which may have been costly to generate.<p>If instead you took 5 bits of randomness, you&#x27;d be able to accept anything in 0..26 and would only have to reject 27..31, which means only rejecting 5&#x2F;32 (15.625%) of the time.<p>0..8 is a particularly bad case, though. If you need numbers in the range 0..14, then it&#x27;s not worth trying to use 5 bits.

## 17613981 by bmm6o

n uniformly random from what distribution?  Or are you taking a limit somewhere?

## 17614702 by emmanuel_1234

Or in O(1):<p><pre><code>  return min
</code></pre>
Alternatively<p><pre><code>  return max</code></pre>

## 17616574 by jgtrosh

For any power of two m, then for any range size n (with m&#x2F;2 &lt; n &lt;= m), the probability of rejection is (m-n)&#x2F;m. If any n is equally probable, then the average rejection is equal to the rejection of the average n (= 3*m&#x2F;4): (m&#x2F;4)&#x2F;m = 1&#x2F;4. This is true for any power of two m. I stand my case!

## 17617717 by dahart

&gt; Or in O(1)<p>You mean in one instruction? The parent comment is O(1). The methods in the article are all O(1) too.

## 17648399 by throwaway080383

Hm, yeah not sure what I was thinking. Maybe expected number of attempts?

