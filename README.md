## What and why?

In the game Elite: Dangerous, the players are able to explore a mockup of the Milky-Way Galaxy. This virtual galaxy, much like real spiral galaxies, have great variability in the stellar density throughout its volume. While parts of the algorithm used by the game to generate the galaxy are known, such as the fact that the algorithm uses an octree-like way of organizing itself and that while generating systems, "mass" and "metallicity" are passed down to smaller and smaller chunks in the octree-like generation process known as "boxels". However, it is not known how exactly the density varies over the volume of the galaxy and there are no clear ways of calculating it, leaving us with only the option of measuring it. 

A way to measure this density are "density column surveys", where a commander uses their navigation panel to know the number of systems within 20Ly of their current star system or the closest 49 systems to their current star system - limitations posed on us by the in-game navigation panel behaviour. This is able to give us a precise value of density at a precise point in the galaxy. However, these densities, by their nature, are only ever able to describe the stellar density for a region of space up to 40Ly in diameter. In addition, producing one of these datapoints takes a fair amount of time - factoring in the hyperspace jump, counting of the stars in the navigation panel and entering the data, each datapoint takes between 1 and 2 minutes if ignoring all other exploration activities. 

### Therefore, a quicker way of gauging stellar density would be preferable. 

Density NavRoute Survey is one such alternative method for measuring the galaxy's density, with some caveats that we shall get into shortly. The base idea of a Density NavRoute survey relies on the fact that the in-game automatic hyperspace routing algorithm has a greedy "fastest route" option. It is important to understand that while this algorithm is unlikely to get **the** optimal solution as the search space is simply too big for the algorithm to do an exhaustive search, we can still be quite sure that it will get a solution that is quite close to the optimal path. As such, we simply assume as if it finds the optimal path. 

## What would an optimal path be like? Lets start with a single optimal jump...

The best **single** jump one could do to get closer to their destination is a maximum jump range jump directly in the direction of the destination. All other paths would result in a longer total path length towards the destination. This is the greedy/naive shortest path algorithm, and for now, we assume the route planner to be a router that uses this strategy. 

In reality, it is exceedingly unlikely for there to be a star system at exactly the right location for this perfect jump to be possible. Therefore, the path will almost always end up diverging from this perfect path. The actual best possible jump will have a jump distance less than the vessel's maximum jump distance and an angular divergence from the optimum. Therefore, we can observe a kind of "squigglyness". An apt term to consider here for this squigglyness is **Tortuosity**, and this tortuosity is the reason why we get information about the stellar density from this method.

A caveat here to wonder about is whether the route plotter does any looking ahead and adjusts the course for a better route? The answer to this is... **Most certainly**. In regions of sparse stellar density in the galaxy, the route plotter will often have to find a route that circumvents a void - a large swathe of completely empty space. In such cases it can be observed that the route planning diverges from this assumed naive shortest path many jumps before reaching the precipice of the void. For now this caveat will not be dealt with as it is an edge-case, however there are ways to combat this which is talked about at the end.

Another question to wonder about is whether the route plotter might also be optimizing for fuel usage? It is well known that longer jumps consume exponentially more fuel up to the Frameshift Drive's maximum fuel consumption limit, which sets the maximum jump range for the vessel. If the route to the destination doesn't require the use of maximum range jumps because the last jump would end up being a short one, then it might make sense to jump slightly smaller distances in order to save fuel, and consequently, time on refuelling by fuel scooping. Fortunately, this question is easily answerable by observing the behaviour of the route planner in-game. When creating navroutes, it can be observed that the planner **does not** optimize for fuel usage. Often the last jump in the route (or indeed, before a neutron-star boost system in the route) ends up being quite a bit shorter than the rest of the jumps in the route because the router tried to get as close to the destination as possible before the last jump, suggesting that it does not care to "spread out" jumps for better fuel economy. 

## With these assumptions, we can start to produce a methodology.

First up, we need to disable neutron-star boosts. Neutron star boosts will cause the route planner to prefer going to neutron stars, even if they are a fair bit out of the way. This completely invalidates our assumption that generally speaking the route planner tries to go for the aforementioned "optimal jump". In addition, for data collecting purposes, the route planner works **a lot** faster with neutron star boosts disabled, allowing us to collect more samples faster. Naturally, we need to make sure the router is set to "Fastest Routes".  We will also want to make sure that no filters are set on the route. All of these settings together means that the route planner should be working as close to trying to make the naive shortest path as possible. We must also be careful of any permit-locked regions of the galaxy, as it is known that the route planner has trouble around these regions and will often make extremely suboptimal routes. Following this methodology, we can build up large amounts of samples for analysis. 

### Analysis method 0: Some very important caveats

No matter which of the following methods we are going to use, there is a caveat to keep in mind with the numbers one gets. **The star systems are ultimately randomly distributed**. This means that no matter how we analyse our data, we must be aware that a single leg within a navroute **can not** be considered by itself alone. The reason for this is because at any given leg, a star just simply might have happened to be generated in the perfect position for the router to route through. Conversely, a small, local void as a result of randomly not having many/any stars generating in a region could cause the router to have a particularly poor single jump. In later analysis, these outliers as a result of randomness would appear as potentially massive spikes or moderately large dips in stellar density. As a result, there is **no** way around needing more information about a datapoint. This can be achieved in one of two ways (or both at the same time, of course):
* More samples, from differing directions, ideally from different jump ranges. Because we are dealing with randomly generated star positions, then we can be sure that the law of large numbers applies. Which is to say, the more samples there are, the closer to the average of our samples gets to the real average. More real samples, is simply better.
* Smoothing of the data. It is basically unfeasible for us to get multiple samples from even a 100x100x100Ly cube everywhere in the galaxy (there are on the order of 16 to 17 **million** of such cubes in the navigable galaxy in Elite: Dangerous). Therefore, we must be content with the fact that most areas are going to have only a single route going through them, if any. So we must work with the single route that we have of the area. In this case, we should simply assume that the density doesn't change abruptly. Unfortunately this is not always true, as can be observed in-game when stumbling upon a dense boxel next to a sparse boxel. Some ways to maybe combat this are talked about at the very end.

In addition, the jump range of the vessel that is doing the surveying matters. Different maximum jump ranges are more or less sensitive to different frequency component ranges of the underlying stellar density. Shorter jump ranges are better at producing more detailed data at a higher spatial resolution, but at the same time are worse at gauging the density of sparser regions of the galaxy. Longer jump ranges, conversely, are better at measuring sparser regions of the galaxy but will fail to give detailed information at smaller scales. This is a trade-off we do by choosing what jump range the vessel has when plotting navroutes. 

### Analysis method 1: Simple error tracking and tortuosity

We can simply track how much shorter and how much of an angle there is between the ideal jump and the actual plotted jump. The ratio of actual jump distance to maximum jump distance along with the angle between jump direction and ideal jump direction give us a measure of "error" from the ideal jump. A simple way to combine both the angle and distance jumped into a single value is to consider the scalar projection of the real jump vector onto the ideal jump vector (or indeed, onto the vector from current position to the route destination system).

A kind of modification on simple error tracking strategies is to specifically calculate the local tortuosity at any given point. This method is more agnostic towards the route plotter looking ahead and avoiding voids as it would not care where exactly the route destination is, only whether the route around the current "sample" has high variance from a straight line in the local region or not, indicating sparser or denser stellar density regions. Low frequency components of tortuosity are also able to detect when the route plotter has made a correction in its routing, for example to avoid a void. In addition, the derivative of tortuosity can help us detect how rapidly the density could be changing, thus potentially giving us a signal for when to be more careful with how higher frequency components are processed for the sample.

Either of these measures can then directly be considered as a measure of density. The exact mapping function between the error and real density would have to be produced by fitting the results to ground truth data. For example, we could use an area of space with many density column survey datapoints to essentially "calibrate" this error-tracking strategy. 

A problem that either of these measures suffer from, is the sensitivity to the vessel's jump range. Different jump ranges will subtly disagree on the error and/or tortuosity of any given region. Lower jump ranges would generally find higher error rates and tortuosity than longer jump ranges for any given density. For example, in a region of moderate stellar density, a vessel with a jump range of 40Ly would find the route to have higher tortuosity than a vessel with 80Ly jump range on the account of the 80Ly vessel having to take less jumps. The 40Ly vessel would also have a higher error rate on the account of having to perform more jumps in the same distance interval and on average having to diverge from ideal path. Therefore, to use these methods directly, some form of correction term would have to be produced based on the vessel's jump range.

### Analysis method 2: Spherical intersection volumes

The navroutes do also produce a wholly different way to get stellar density information though. The spherical intersection volume method can give us **precise** stellar density information for a region of space. Lets start with a goal for our vessel to go from its current star position to a target star position in as short of a route as possible.

![](readme_images/Pasted%20image%2020260211131638.png)

If we project a sphere from the coordinates of the star system the vessel is attempting to find its next leg of the journey from with a radius equal to the vessel's maximum jump range, then every star that falls within this sphere is a valid target for the next jump. 

![](readme_images/Pasted%20image%2020260211131929.png)

Next we project a sphere from the final destination system's coordinates. The surface of this second sphere represents the collection of equidistant points from the destination system, meaning the shortest path. Now, all we have to do, is uniformly scale up the destination system sphere until it reaches the point where the sphere's surface intersects a system that lies within the vessel's jump range sphere. The first such system that falls within the vessel's valid jump targets and intersects with the surface of the destination sphere **is** by definition the most optimal single jump towards the route's endpoint that can be done if using the naive shortest path algorithm. 

![](readme_images/Pasted%20image%2020260211132150.png)

The two spheres that are now intersecting produce an intersection volume. It is guaranteed that there are no stars within this intersection volume, except for the one star that is located somewhere on the surface of this volume. This produces a lensoid shaped intersection volume and because we know there is exactly one star per this volume, we know the local density.

![](readme_images/Pasted%20image%2020260211132351.png)

Just like the error tracking method, this method does suffer from a slight error if the route plotter has to circumvent a void / extremely sparse region larger than the vessel's jump range, because in those cases, the plotter has to necessarily intentionally diverge from our assumed naive shortest path. Using the local tortuosity measure could perhaps be used to produce a correction term for this error, but about that much later. 

A big boon for this method however, is that unlike the first method, this method doesn't require a mapping function based on some ground truth data as the exclusion zones **are** ground truth data on their own. Of course, ground truth data from other sources is still invaluable for verifying the whole model. In addition, this method is jump-range agnostic by default. The intersection volume already does the "normalization" between jump ranges for us, as shorter jump ranges produce smaller jump range spheres for the destination sphere to intersect with. 
### Warning: Noise
Both of the aforementioned methods do suffer from one major hurtle to overcome - noise. As you might have noticed with the exclusion volumes method, the exclusion volume is almost always significantly smaller than the vessel's jump range volume. And because we are probably not interested in the stellar density specifically in the area of the exclusion volume, but rather at a larger scale, then we need to extrapolate the acquired density to larger scales. This produces a problem however. 

**What if a star just simply happens to be generated very close to the ideal jump point?** We would get an arbitrarily high density value! First way to combat this is simple filtering... We know that there isn't going to be a region of space that has a stellar density of... say 20 stars/ly^3... So we can safely ignore any density value above this. However, this doesn't really help us a whole lot, because we still do not want to see a sudden spike in density in the middle of a void, as it is almost certainly noise and not a real signal. So, we **will** have to employ smoothing to our data as well. 
## Calculations
### Distance between any two stars
To get the distance between any given two stars in the route we simply use Pythagorean theorem. Our coordinates have 3 components, therefore... 

![](readme_images/Pasted%20image%2020260209142934.png)

d = sqrt((x_1 - x_2)^2 + (y_1 - y_2)^2 + (z_1 - z_2)^2)

### Maximum jump range of the vessel

We will need to know the surveying vessel's jump range. Using the "Loadout" event from a player journal, it is possible to get the information about the weight, max fuel, FSD type and any engineering modifications applied to the FSD. Based on this, current maximum jump range can be calculated using the "fuel equation". 

Unfortunately, while this approach would give us a very close, if not the exact current jump range of the vessel, the router seems to either be somewhat smart or there is some hidden factor at play. If we were to find the maximum jump distance in a long navroute, we would find that it likely slightly exceeds the calculated maximum jump range! Either the plotter is smart enough to know when the vessel is incapable of refuelling and therefore understands that the next jump can be longer, or there is some other weird hidden factor at play here. 

As a result, until this mystery is solved, we have to choose the maximum jump range based on the longest jump in the navroute. Asking the player to enter their maximum jump range also does not work because the game reports the same maximum jump range that can be calculated using the fuel equation. 

Using the largest jump distance in the navroute as the maximum jump range does come with the caveat that if the whole route lies within a sparse stellar density region, then the maximum range might be significantly smaller than the actual maximum jump range, skewing the acquired density values greatly. For that reason, for now, diligence is required when collecting data. The 3rd party application that aids in collecting this data should report the maximum jump distance it found for the generated navroute. The commander collecting the data should then verify that it is close enough to the actual maximum jump range. I **almost** arbitrarily propose a maximum jump range deviation cutoff of 0.2Ly for the moment. 

**Suggestions from the galactic community on how to find the vessel's maximum jump range for any given navroute are most welcome as any error in this value is compounded by the cube!**

### Exclusion volume and density

To get the density values, we need to figure out the exclusion volume. The exclusion volume is produced by two spherical domes/caps joined together. One produced by the max jump range sphere, and the other by the sphere to the route destination. This makes it relatively easy to calculate the volume.

Volume of a spherical cap is given by the formula:

![](readme_images/Pasted%20image%2020260209140726.png)

V = 1/3 * pi * h^2 * (3 * r - h)

Where:

**r** is the radius of the sphere for which the spherical cap is calculated for

**h** is the height of the spherical cap from the base to the central high point of the cap, which we can find by first calculating the distance to the sphere intersection plane **d_i** with the formula:

![](readme_images/Pasted%20image%2020260209154154.png)

d_i = (d^2 + r_1^2 - r_2^2) / (2 * d)

From which, we get **h** by simply subtracting the intersection plane distance from the radius of the sphere:

![](readme_images/Pasted%20image%2020260209154229.png)

h = r - d_i

Where:

**r_1** is the radius of the sphere for which you are calculating **h** for

**r_2** is the radius of the intersecting sphere

**d** is the euclidean distance between the centers of the two spheres

Therefore, the full exclusion volume is given by adding together the volumes of the spherical caps produced by the max jump range sphere V_1 and the destination sphere V_2

![](readme_images/Pasted%20image%2020260209141306.png)

V_ex = V_1 + V_2

Because we know that at the very edge of this exclusion volume there is exactly 1 star, then we can assume that there is 1 star per exclusion volume in the particular area of the galaxy. Which means, to get the actual density, we simply take the reciprocal of the exclusion volume:

![](readme_images/Pasted%20image%2020260209142610.png)

rho = 1 / V_ex

#### Exclusion volume centroid

Once we have calculated the stellar density, we must decide what part of space does this density actually apply to. Because we have calculated the density based off a lens-like exclusion volume in space that has a definite location, then the the only natural conclusion is that the density applies to a point somewhere within the exclusion volume. 

The first and most logical position to consider for the density is the "center of mass" of the lensoid. While it **is** possible to calculate this point, in most cases it will lie somewhere fairly close to the "bounding box center" point of the lensoid. Both the center of mass and the bounding box center are guaranteed to lie on the line that forms between the highest points of the spherical caps as a result of spherical symmetry. In addition, since other parts of analysing this data produce vastly more uncertainty in the results than this miniscule difference in the real centroid point against the proposed bounding box center, then at this time, for the sake of simplicity, the bounding box center shall be used.

Since we know the heights **h_1** and **h_2** of both spherical caps from our previous calculations, then to get the height to the bounding box center we can use the following formula:

![](readme_images/Pasted%20image%2020260209152424.png)

h_c = (h_1 + h_2) / 2

Next we can figure out how far from the jump start point the bounding box center is by simply subtracting this height from the maximum jump range, since the bounding box necessarily "starts" from the point of the "ideal jump":

![](readme_images/Pasted%20image%2020260209154758.png)

d_c = r - h_c

Where:

**r** is the maximum jump range (the radius of the jump range sphere)

Next we need to find the direction towards the ideal jump. First we find the directional unit vector with the formula:

![](readme_images/Pasted%20image%2020260211202146.png)

Where:
**p_1** is the coordinate vector of the star system the jump is being initiated from

**p_2** is the coordinate vector of the route's end point

Then, to get the vector for the bounding box center:

![](readme_images/Pasted%20image%2020260209162151.png)

The resulting vector **b** is the location of the center of the bounding box and the point around which we consider the previously calculated stellar density to exist. 

### Smoothing and filtering

As alluded to in the opening portions of this little "whitepaper", the exclusion volume based density measure has a slight problem. Namely, noise can affect the density measure to an almost arbitrarily great degree. The problem is less severe for noise causing low density, as a low density is more akin to a real signal (the void the vessel is sensing is **actually** there!). But noise causing higher densities can actually produce arbitrarily high densities due to the the possibility of the intersection volume to be arbitrarily small.

![](readme_images/Pasted%20image%2020260210004153.png)

lim(V_ex→0), 1/V_ex = inf

The easiest to conceptualize way of solving this problem is to smooth by taking the average of the densities around the current exclusion volume point. Essentially, we would employ a "moving window", or **kernel** based smoothing. 

#### Lets find the kernel's center point

First question to solve is to figure out where the center of the kernel should lie. Since we are smoothing a value that describes a definite area in space, then it makes a lot of sense to smooth based on this very same area. In our case, that means the centroid of the exclusion volume.

The centroid of the exclusion volume will **never** coincide with the destination star's location (apart from the case of the theoretical best possible jump) and will **always** have a greater magnitude from jump start position than the next star's position in the navroute. The projection of the centroid location onto the current navroute leg path will always lie somewhere beyond the jump's destination star. These are all consequences of how the exclusion volume is created in our case. So one might think to project the centroid onto the navroute's next leg's path. Unfortunately, depending on the angle under which the navroute's next leg is compared to the vector from current system position to the centroid position, the projected location can be on either side of the jump destination star. This approach clearly does not work as is. 

**Suggestions from the galactic community on how to determine the most logical kernel center point are welcome!**

For now, I arbitrarily propose to do a scalar projection of the centroid position onto the jump vector. 

![](readme_images/Pasted%20image%2020260211145609.png)

s = (c dot d) / norm(d)

Where:

**c** is a vector from jump start system to exclusion volume bounding box center (the centroid). 

**d** is a vector from jump start system to jump destination system.

Then the difference between the magnitude(norm) of the jump vector and the result of the scalar projection is then used to move in the direction of the jump after the current one. 

![](readme_images/Pasted%20image%2020260211150549.png)

k = (s - norm(j)) * u

Where:

**u** is the unit vector from jump destination system towards the destination system after it.

**j** is the coordinate vector of the current jump start system. 

**k** then, is the coordinates to the kernel center point. 

This way is probably **not** the correct way to do find the most apt location for the kernel center point. Suggestions are welcome.

#### Finding the average density

Next, to find the average, we integrate the density values over half of the kernel size in both the forwards and backwards direction of the navroute path and then divide the result with the full size of the kernel to get the average density value around the centroid location. 

![](readme_images/Pasted%20image%2020260211151726.png)

D = int from {k - (w/2)} to {k + (w / 2)} of S(x)dx

Where:

**k** is the center point of the kernel on the total path distance of the navroute

**w** is the width/size of the kernel

**S(x)** is the sampling function. This will have to be some interpolation function between the known density values on the path. A logical fit is linear interpolation.

This "density over distance" value is not yet our average, as we need to get rid of the "over distance" part of the value. Luckily, because we know exactly how large the kernel was that was used for integrating, then we can simply divide this value by the kernel window size, and we will get the average density back. 

![](readme_images/Pasted%20image%2020260211152400.png)

rho = D / w

**We have now found the average density using "path-distance" kernel window**

##### But exactly how wide is the kernel?

At this point, the only unfixed variable of the methodology is the kernel size. So how **do** we choose this kernel size?

**The Rayleigh Criterion** lays down a widely accepted criterion for determining the maximum resolving capability of an imaging system. At risk of sounding like getting lost in abstractions and analogies, I would like to posit that in this survey's context we are trying to "image" the density fluctuations. 

![](readme_images/Pasted%20image%2020260211153242.png)

theta_min = 1.22 * (lambda / D)

Where:

**theta_min** is the angular resolution of the smallest resolvable feature

**lambda** is the wavelength of the wave used to image the features (usually electromagnetic radiation but could, for example, also be the Broglie wavelength of an electron)

**D** is the size of the aperture of the imaging device.

Because we have no such thing as an "aperture" in this abstract imaging setup, then the only thing we can change to resolve finer details is the "wavelength". Naturally, this wavelength is our vessel's jump range. However, to produce a "wave-like" characteristic for sampling with our vessel, we will need **two** samples per wavelength as the **Nyquist-Shannon Sampling Theorem** demands. Therefore, translating all of this to our Rayleigh Criterion equivalent:

![](readme_images/Pasted%20image%2020260209230353.png)

Where:

**D_min** is the minimum distance between resolvable density features in light-years

**R** is the maximum jump range of the vessel in light-years

**D** is the aperture size... In our case always 1? **If the galactic community finds an analogue to the aperture size in this abstract imaging setup then it would be interesting to consider the implications to the methodology.**

Consequently, if we wish to attempt to "image" these feature sizes, then that is exactly the size of the smallest kernel we can have. It is important to note here that while it is not possible to resolve features smaller than this with a single navroute, any extra navroutes that go through the same general area of space would add to the overall resolution of the local area. As said earlier, more samples in any given area of space is **always** better. 

##### The literal edge cases

Because these kernels are **centered** on some distance along the route being analysed, then the obvious question arises about what exactly happens when the kernel has to sample the path at the very beginning or end of the path? The range that the kernel tries to sample might literally not exist in our route! Several **extrapolation** strategies exist to deal with these edge cases.
* We could simply repeat the end point value beyond the end point.
* We could take the average of n points closest to the end point and set that as the value beyond the end point.
* We could pseudo-randomly add some jitter to either of the former values.
* We could pseudo-randomly pick values from among the n points closest to the end point.
* We could mirror the necessary amount of values from the end points.
* We could truncate the kernel windows.
* And many... many others...

While intuitively some pseudo-random jitter based strategy could perhaps get the best generated data out of these, it would mean sampling made-up data regardless. It is more honest to simply truncate the kernel window size in these edge cases. If this is the case, then the **w** value must be reduced according to the reduction in the kernel window size, when calculating the average density. 

## Real data

It is time to put this whole system to test.

A set of navroutes from `Skueqoo KO-M c22-0` to `Spooroa XK-C b40-85` was generated. Disabling the vessel's *Guardian frame-shift-drive booster* and hinting to the router that you intend to carry cargo can give us a few different maximum jump-ranges to compare between. Though it is important to note here that any change in the vessel's jump range will most likely cause the route to diverge from other routes.  As per the methodology requirements, jet-cone boosts were turned off and all filters from the route were removed.

This route starts from the edge of the galaxy, somewhat below the galactic plane, and goes in the direction of Sagittarius A*, ending at the precipice of the galactic core. The route is almost 20000 light-years in euclidean distance and goes through two galactic arms and "voids" between them and the galactic core. This route should give us a good amount of variety in the data to compare against.

![](readme_images/route_in_game.png)

Route as seen in-game.

With our vessel in the maximum jump range configuration, we get:

![](readme_images/Pasted%20image%2020260211162751.png)

**Notice the logarithmic scale for density**

As predicted, the raw signal is quite noisy. However, regardless of the noise, we can most certainly make out the galactic arm centered around 7000ly path-distance, the void between the galactic arms centered around 11250ly, the next galactic arm centered around 16250ly, a tiny slightly sparser region at around 18000ly and then the beginning of the galactic central region from around 18750ly. 

Now lets apply our proposed Rayleigh-distance averaging.

![](readme_images/Pasted%20image%2020260211165445.png)

This certainly looks much better with high frequency peaks generally smoothed out. However, if we look a bit more closely, we can notice some artifacting. Namely, it would appear that the smoothing consistently produces values that are closer to the peaks of any high-frequency noise. The reason for this is rather simple. **The density scales exponentially, but averaging is a linear operation**. Essentially, a single high-density peak from noise will have much more "power" over the lower density samples that might be around it. 

An easy way to adjust our averaging method for this asymmetry is to use harmonic averaging instead. This would suit especially well, as it is a simple modification to our already described averaging methodology.

![](readme_images/Pasted%20image%2020260211175723.png)

And

![](readme_images/Pasted%20image%2020260211175814.png)

This results in the following:

![](readme_images/Pasted%20image%2020260211174917.png)

Yet another step in the right direction!

In-fact, for now, I call it good enough. Perhaps a multi-scale harmonic average would be even better. And yet another strategy to employ would be to move from a uniform kernel to a gaussian one. 

**Suggestions on strategies for smoothing are welcome from the galactic community**. 

Next we need to verify the results. Currently, there has been no verification comparing this method to the density column survey method, however in the future this promises to be the best way to calibrate and verify the density navroute survey method. We **can** however verify our results against our own results. First, lets compare a few different jump ranges:

![](readme_images/Pasted%20image%2020260211185019.png)

Once again, we can definitely see the general trends in the data. 

One might say that this is still extremely noisy data. And it probably is somewhat noisy... However, because we are using different jump ranges, the likelyhood that the route plotter goes though exactly the same space as some other jump range is exceedingly small. So the different jump ranges shown here are each taking a slightly different path through space. And because they are taking a different path through space, they are going to encounter different high-frequency density features. 

Looking at these graphs, it would seem to me that perhaps the galactic arms are actually quite turbulent and have a lot of high frequency density fluctuations within it. In addition, at a few places, we can tell that there might be a large-scale density feature in the way. For example right towards the beginning all routes probably go through a higher density region at around 1000 to 1500ly euclidean distance. And another such feature might exist at around 16500ly euclidean distance. Also, all jump ranges agree on the void between galactic arms being present, as well as the extremely abrupt start to the galactic central region. 

At this point, it would make sense to also visually confirm whether these values seem self-consistent. First lets look at whether the density around 5000 ly euclidean distance matches that of around 13500 ly euclidean distance.

![](readme_images/Pasted%20image%2020260211190305.png)

5000ly

![](readme_images/Pasted%20image%2020260211190822.png)

13500ly

While in the background of the 13500ly image we can definitely see "more stars", the actual local density is about the same! Both images are taken at the same "zoom level", and both have 11 systems shown as the close systems to the cursor! (I understand you have to take me at my word here, but I promise I simply moved close to the path until checking a star's current distance (the euclidean distance to the route start) showed the required distance) We would expect an area with double the stellar density to then have double the star names on the screen. Lets see if this hypothesis holds. Stellar density at 5000ly is roughly 0.000669. So lets go to an area with a stellar density of 0.001338. The area between the second galactic arm and the core region at 18350ly seems to suit just fine.

![](readme_images/Pasted%20image%2020260211191438.png)

18350ly

We can see 22 systems with names... **exactly** what we predicted. 

**As a side note... Counting systems (or the blue circles the project onto the cursor's plane) in the galaxy map seems to ALSO be a viable way to get quite good density data! "Density GalaxyMap Survey" next?** Though this way of surveying density also has the problem of manual counting and data entry... the two problems that this very survey type is trying to solve.

I admit, there is quite a lot more scrutiny and optimization that can still be put into this type of survey, but as a proof of concept, I hope I have been able to demonstrate that this way of measuring the galaxy's density is possible and gives real, tangible results. 

## Thank you

If you got this far, thank you for sticking with me. I hope it wasn't too difficult, or too easy of a read and that you find the methodology so far acceptable.

If you have any suggestions or comments or constructive criticism, congratulations or anything else, then I will be more than happy to hear them out either in-game (CMDR Clanga) or on Discord, in any of the Elite: Dangerous related groups I am in (Fleetcom feels most apt), I will be reachable with @Clanga handle on Discord. 



## Extra things to think about

### Tortuosity

Tortuosity is a property and measure of how complex, windy and constricted pathways through a bulk material are. It defines how well and easily something can be transported through a porous bulk material. This has a direct analogy to our problem space. Our vessel is something to be transported through a bulk material. The bulk material is the galaxy itself. Stars in the galaxy create a densely connected graph which represents the pathways through the bulk material in our case. And the navroute is the shortest path through this porous material. In real physical materials and systems described by tortuosity, constrictions in pathways are a strong factor to have to consider. However, in our case, there are effectively no constrictions in our pathways through the bulk material - our vessels do not have any more difficulty jumping into one system over another. However, as an extra point to wonder about is whether this concept of "constrictions" in the bulk material could be considered the fuel cost of the jump. If so, then perhaps "Economic Routes" routing option could be worked into being a possible way to gauge stellar density as well. 

 In the context of the density navroute survey, tortuosity is a proxy measure for two things:
* How much stellar density there is in the region of space (higher tortuosity values would suggest a sparser stellar density region)
* How much variance there is at fine scales in the region of space (higher tortuosity values could suggest that voids are interlaced with higher density regions)

A simple measure of tortuosity is the ratio of the real path length to the euclidean straight path thought the medium. We will use this very measure to get our tortuosity at any scale we want to get the tortuosity for. Note that tau stands for tortuosity in this section, and is not equal to 2pi.

![](readme_images/Pasted%20image%2020260209162958.png)

tau = d_p / d_k

Where:

**d_p** is the total distance travelled between the two points that form **d_k**

**d_k** is the euclidean distance **kernel**. 

The derivatives of these resulting tortuosity values can also give us information about transition regions for the density.
* negative derivative values of tortuosity mean that the vessel is in a transition region towards a higher density and moderate increases in density can be considered more truthy.
* positive derivative values of tortuosity mean that the vessel is in a transition region towards a lower density and moderate decreases in density can be considered more truthy.

And finally, integrals of the derivatives of the tortuosities over space at different scales can give us a measure of how much variance in the tortuosity, and as a proxy density, values there are in the local area of space. This could then be used as a measure and signal to adjust the amount of smoothing done on the density values in areas of high variability, as the fluctuations in density are more likely to be a real signal. 

To get a better understanding of how to apply the produced tortuosity data to smoothing the density, lets produce a set of behaviours described by different values of tortuosity at different scales

*Large scale:* **Low**
* *Medium scale:* **Low**
    * *Small scale:* **Low** 
        * The vessel is currently in a high density region. The current sample is not significantly different from the rest of the local region. The density value can be trusted more or less fully. 

	* *Small scale:* **High**
        * The vessel is currently in a high density region . The current sample is significantly different from the rest of the local region. The density value should be smoothed.
* *Medium scale:* **High**
	* *Small scale:* **Low** 
		* The vessel is currently in a region of varying density. The current sample is somewhat different from the rest of the local region. The density value should be slightly smoothed.
	* *Small scale:* **High**
		* The vessel is currently in a region of temporary low density. The current sample is not significantly different from the rest of the local region. The density value can be trusted.

*Large scale:* High
* *Medium scale:* **Low**
	* *Small scale:* **Low** 
		* The vessel is currently in a region of temporary high density. The current sample is not significantly different from the rest of the local region. The density value can be trusted.
	* *Small scale:* **High**
		* The vessel is currently in a region of varying density. The current sample is somewhat different from the rest of the local region. The density value should be slightly smoothed.
* *Medium scale:* **High**
	* *Small scale:* **Low** 
		* The vessel is currently in a low density region. The current sample is significantly different from the rest of the local region. The density value should be smoothed.
	* *Small scale:* **High**
		* The vessel is currently in a low density region. The current sample is not significantly different from the rest of the local region. The density value can be trusted more or less fully. 

**Could tortuosity add efficacy to the way we smooth our density values?**
