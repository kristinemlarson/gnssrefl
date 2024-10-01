exit
clear all
close all
clc
%https://www.mathworks.com/matlabcentral/answers/1694690-how-to-save-figure-frames-as-gif-file
FS = 12;
% min and max elevation angles (degrees)
emin = 5;
emax = 20;
% range of angles to use in the simulation
E = emin:0.05:emax;

% Normalizing to amplitude of 1.   
Am=1;
% use simple attenuation parameter.
% more realistic ones can be generated from the Nievinski simulator,
% but that has added complexity of surface type.  Here I am only
% trying to show what is generating the frequency changes (which are 
% directly related to reflector height.
attenuator = true;

% Setup to make movie
fig1=figure(1); % Create figure handle
set(gcf,'defaultaxesfontsize',FS)
winsize = get(fig1,'Position'); % Get Window Size
winsize(1:2) = [0 0];
incr = 10;
numframes = floor(length(E)/incr);
disp(['Number of frames'  num2str(numframes)])
 
set(fig1,'NextPlot','replacechildren') % Ensure each plot is the same size

gifFile = '/Users/kristine/Downloads/myAnimation.gif';
exportgraphics(fig1, gifFile);

 
for height = [4, 10]
    [startX, bigNumber, Xaxis, Yaxis, SNR] = set_Frame(height,E,Am,attenuator);
  for i=1:numframes
    index=i*incr;
    k=1:index;
    % how away is the reflected signal on the xaxis
    Xd = height/tand(E(index));
    % where does the direct signal start from
    X3 = startX - Xd;
    subplot(2,1,1)
    % GPS antenna is black, reflected signal is red, direct signal is blue
    plot([0 (0 + bigNumber*cosd(E(index)))], ...
        [height (height + bigNumber*sind(E(index)))], 'b-', 'linewidth',2);hold on;
      plot(  [startX Xd 0], [X3*tand(E(index)) 0 height], 'r-',... % reflected signal
        'linewidth',2); hold on;
      plot([0 0], [0 height], 'k-', 'linewidth',2); hold on;
      plot(0, height, 'k^','markerfacecolor','k','markersize',10); 
      hold off;
 
    xlim([-1 Xaxis]), ylim([0 Yaxis])
     
    legend('Direct Signal', 'Reflected Signal', 'Antenna','Location','NorthWest')
     grid on;
    xlabel('meters'), ylabel('meters')
    title(['GNSS Reflection Geometry'],'FontWeight','normal');

    subplot(2,1,2)
    
    plot(E(k), SNR(k),'k-')
    xlim([emin emax]),   ylim([-2 2])
    xlabel('Elevation Angle (deg)')
    title(['H = ' num2str(height) ' meters-Simulated GPS L2 SNR Data'],...
        'FontWeight','normal')
    ylabel('Volts/Volts')
    grid on

    
    exportgraphics(fig1, gifFile, Append=true);
  end
end
return


  