function [startX, bigNumber, Xaxis, Yaxis, SNR] = set_Frame(height,E,Am,atten)
%function [startX, bigNumber, Xaxis, Yaxis, SNR] = set_Frame(height,E,Am,atten)
% height - vertical distance of antenna phase center to surface
% E elevation angles in degrees
% Am amplitude of the multipath
% atten boolean if you want to attenuate amplitude as elevation angle increases
%
% returns some geometric values for the plot and the simulated SNR data in 
% variable with that name

wavelength = 0.244; %GPS L2 wavelength

% this is how much longer the reflected signal (red) travels than
% the direct signal (blue)
path_del = 2*height.*sind(E);
psihat = 2*pi*path_del/wavelength;   % radians

% simple attentuation
if atten
    Am = 5*Am./E;
end

% this is the definition of SNR data
SNR = Am.*(cos(psihat) + sin(psihat));

Xaxis = ceil(height/tand(5));
Yaxis = 0.33*Xaxis;
% just so the ray comes from outside the plot, which is what i want.
% made up number
startX = 30*height; 
bigNumber = 20*height;
